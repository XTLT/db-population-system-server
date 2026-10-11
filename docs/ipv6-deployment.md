# IPv6 + DDNS 部署指南

本指南帮助您通过 IPv6 + 域名 + DDNS-go 实现移动端与服务器的通信。

## 前提条件

1. 服务器有公网 IPv6 地址
2. 拥有一个域名
3. 域名 DNS 支持配置 AAAA 记录（IPv6）

---

## 第一步：获取服务器 IPv6 地址

```bash
# 查看 IPv6 地址
ip -6 addr show

# 或使用 curl 测试
curl -6 ifconfig.co
```

记录您的公网 IPv6 地址，例如：`2001:db8::1`

---

## 第二步：安装 DDNS-go

### 方法一：Docker 部署（推荐）

```bash
docker run -d \
  --name ddns-go \
  --restart=unless-stopped \
  --net=host \
  -v /opt/ddns-go:/root \
  jeessy/ddns-go
```

### 方法二：直接安装

```bash
# 下载最新版本
wget https://github.com/jeessy2/ddns-go/releases/download/v5.6.0/ddns-go_5.6.0_linux_x86_64.tar.gz

# 解压
tar -zxvf ddns-go_5.6.0_linux_x86_64.tar.gz

# 安装服务
sudo ./ddns-go -s install

# 启动服务
sudo systemctl start ddns-go
```

### 配置 DDNS-go

1. 访问 `http://服务器IP:9876`
2. 选择您的 DNS 服务商（阿里云、腾讯云、Cloudflare 等）
3. 填入 DNS 服务商的 API 密钥
4. 配置域名：
   - IPv6 启用
   - 域名：`api.yourdomain.com`
5. 保存配置

DDNS-go 会自动检测 IPv6 地址变化并更新 DNS 记录。

---

## 第三步：配置域名 DNS

在域名服务商控制台添加 AAAA 记录：

| 记录类型 | 主机记录 | 记录值 | TTL |
|---------|---------|--------|-----|
| AAAA | api | 您的IPv6地址 | 600 |

DDNS-go 会自动更新此记录。

---

## 第四步：配置防火墙

```bash
# 开放 HTTP 和 HTTPS 端口（IPv6）
sudo ip6tables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo ip6tables -A INPUT -p tcp --dport 443 -j ACCEPT

# 保存规则
sudo ip6tables-save > /etc/iptables/rules.v6
```

---

## 第五步：部署应用

### 1. Docker 方式

```bash
# 启动 Docker IPv6 支持
# 编辑 /etc/docker/daemon.json
sudo tee /etc/docker/daemon.json <<EOF
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00:dead:beef::/48"
}
EOF

# 重启 Docker
sudo systemctl restart docker

# 启动应用
cd /path/to/population-system
docker-compose up -d
```

### 2. 直接运行方式

```bash
cd server

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp config.example.yaml config.yaml

# 编辑配置
vim config.yaml

# 启动服务（监听 IPv4 和 IPv6）
python app_modular.py
```

---

## 第六步：配置 SSL 证书（可选）

### 使用 Let's Encrypt（推荐）

```bash
# 安装 certbot
sudo apt install certbot

# 获取证书
sudo certbot certonly --standalone -d api.yourdomain.com

# 证书路径
# /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/api.yourdomain.com/privkey.pem

# 复制证书到项目目录
cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem certs/server.crt
cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem certs/server.key
```

### 更新 Nginx 配置

编辑 `nginx.conf`，取消 HTTPS server 块的注释，并修改证书路径：

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    # ...
}
```

---

## 第七步：配置移动端

### 方法一：App 内修改域名

1. 打开 App，进入 **设置** 页面
2. 点击 **服务器地址**
3. 输入域名：`http://api.yourdomain.com` 或 `https://api.yourdomain.com`
4. 保存并重新登录

### 方法二：修改默认域名（打包前）

编辑 `mobile/lib/config/app_config.dart`：

```dart
class AppConfig {
  // 修改为您的域名
  static String apiBaseUrl = 'http://api.yourdomain.com';

  // 备用域名列表
  static List<String> backupUrls = [
    'http://api.yourdomain.com',
    'http://[2001:db8::1]:5000',  // IPv6 直连（应急）
  ];
  // ...
}
```

---

## 验证连接

### 1. 测试 IPv6 连通性

```bash
# 从客户端 ping IPv6 地址
ping6 2001:db8::1

# 测试 API
curl -6 http://api.yourdomain.com/api/health
```

### 2. 检查 DNS 解析

```bash
# 查询 AAAA 记录
dig AAAA api.yourdomain.com

# 或使用 nslookup
nslookup -type=AAAA api.yourdomain.com
```

### 3. 检查 DDNS 更新

```bash
# 查看 DDNS-go 日志
docker logs ddns-go

# 或
journalctl -u ddns-go -f
```

---

## 常见问题

### 1. 移动端无法连接

- 检查手机是否支持 IPv6（移动网络通常支持）
- 检查 DNS 解析是否正确
- 检查防火墙是否开放 IPv6 端口

### 2. 域名解析失败

- 确认 DDNS-go 服务正常运行
- 检查 API 密钥是否正确
- 确认域名 AAAA 记录已添加

### 3. IPv6 地址变化

DDNS-go 会自动检测并更新，无需手动干预。

---

## 配置文件说明

| 文件 | 用途 |
|-----|------|
| `docker-compose.yml` | Docker 部署配置，已启用 IPv6 |
| `nginx.conf` | Nginx 反向代理，已支持 IPv6 监听 |
| `config.yaml` | 后端应用配置 |
| `app_config.dart` | 移动端域名配置 |

---

## 安全建议

1. 启用 HTTPS（配置 SSL 证书）
2. 配置防火墙，只开放必要端口
3. 定期更新 DDNS-go 和应用版本
4. 使用强密码保护 DDNS-go 管理界面
