# mTLS 部署说明（路线A：stunnel 双向证书校验）

## 架构

```
客户端（桌面端/移动端，内置 client.crt+client.key）
   │  TLS 双向校验（服务器出示 server.crt，客户端出示 client.crt）
   ▼
stunnel（0.0.0.0:5000，verify=2）
   │  明文转发（仅本机）
   ▼
gunicorn（127.0.0.1:5001，无 TLS）
```

- 服务器证书：`data/certs/server.crt`（自签，同时充当 CA）
- 客户端证书：`data/certs/client.{crt,key}`（CN=population-client，由 server.key 签发）
- 客户端校验证书链：client.crt 由 server.crt 签发 → 三端内置 server.crt 校验服务器、出示 client.crt

## 部署步骤（26 已部署，重装/换机参考）

1. 安装 stunnel：`apt-get install -y stunnel4`
2. 生成客户端证书（用现有服务器证书作 CA 签发）：
   ```bash
   cd /root/population-system/data/certs
   openssl genrsa -out client.key 2048
   openssl req -new -key client.key -out client.csr \
     -subj "/C=CN/ST=Local/L=Local/O=PopulationSystem/CN=population-client"
   openssl x509 -req -in client.csr -CA server.crt -CAkey server.key \
     -CAcreateserial -out client.crt -days 3650
   chmod 600 client.key
   openssl verify -CAfile server.crt client.crt   # 应输出 OK
   ```
3. gunicorn 只监听本机（去掉 --certfile/--keyfile）：
   `--bind 127.0.0.1:5001`
4. 放置 stunnel 配置与 systemd 单元：
   ```bash
   cp deploy/stunnel/population.conf /etc/stunnel/population.conf
   cp deploy/stunnel/population-stunnel.service /etc/systemd/system/
   systemctl daemon-reload
   systemctl restart population-server && systemctl enable --now population-stunnel
   ```
5. **必须重新打包三端客户端**（内置 client.crt/client.key + server.crt）：
   - 桌面端：`certs/` 放 client.crt/client.key/server.crt，`_get_ssl_context()` 自动出示客户端证书
   - 移动端：`assets/certs/` 放 client.crt/client.key/server.crt，`SecurityContext` 自动加载
   - 旧版本客户端（无客户端证书）将无法连接——这是 mTLS 的预期防护

## 验证

```bash
# 无客户端证书 → 握手被拒（应失败）
curl -sk https://127.0.0.1:5000/api/health

# 带客户端证书 → 200
curl -sk --cert data/certs/client.crt --key data/certs/client.key \
  https://127.0.0.1:5000/api/health
```

## 回滚（恢复原单 TLS 模式）

```bash
systemctl disable --now population-stunnel
# population-server.service 恢复 --bind "[::]:5000" + --certfile/--keyfile
systemctl daemon-reload && systemctl restart population-server
```
回滚后旧客户端（证书固定版 v0.0.26/v0.0.22）即可连接；mTLS 版客户端（v0.0.27/v0.0.23）仍可连（出示证书被忽略）。

## 故障排查

| 现象 | 原因 |
|---|---|
| stunnel `Error resolving "[::]"` | 机器无 IPv6，accept 用 `0.0.0.0:5000` 而非 `[::]:5000` |
| stunnel `Address already in use` | gunicorn 占用了 0.0.0.0:5000，gunicorn 必须只绑 127.0.0.1:5001 |
| 客户端连接失败 `alert unknown ca` | 客户端证书过期/未内置，需重新打包 |
| 浏览器访问告警 | 自签证书，浏览器需手动信任；客户端内置证书校验不受影响 |
