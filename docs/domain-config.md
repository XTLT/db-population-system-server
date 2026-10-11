# 域名配置说明

## 域名结构

```
<你的域名>    → API 服务地址（移动端访问）
<你的域名>        → 主域名（可选）
```

---

## 第一步：DDNS-go 配置

访问 `http://服务器IP:9876` 进行配置：

### 基本信息

| 配置项 | 值 |
|-------|-----|
| DNS 服务商 | 阿里云 / 腾讯云 / Cloudflare（根据您的域名服务商选择） |

### IPv6 配置（必须）

| 配置项 | 值 |
|-------|-----|
| 启用 | ✅ 勾选 |
| 域名 | `<你的域名>` |
| 获取 IP 方式 | 自动获取 |

---

## 第二步：DNS 记录配置

登录您的域名服务商控制台，添加 DNS 记录：

| 记录类型 | 主机记录 | 记录值 | TTL |
|---------|---------|--------|-----|
| AAAA | www | （自动由 DDNS-go 更新） | 600 |

---

## 第三步：验证配置

### 1. 检查 DDNS-go 日志

```bash
docker logs ddns-go
```

看到类似输出表示成功：
```
IPv6 地址更新成功: <你的域名> -> 2001:db8:xxxx:xxxx
```

### 2. 测试 DNS 解析

```bash
# 查询 AAAA 记录
dig AAAA <你的域名> +short

# 或使用 nslookup
nslookup -type=AAAA <你的域名>
```

应返回您的 IPv6 地址。

### 3. 测试 API 连接

```bash
# IPv6 方式访问
curl -6 http://<你的域名>/api/health

# 应返回
{"status": "ok"}
```

---

## 第四步：移动端配置

### 方法一：App 内修改（推荐）

1. 打开 App → 设置 → 服务器地址
2. 输入：`http://<你的域名>`
3. 保存并重新登录

### 方法二：打包前配置

文件：`mobile/lib/config/app_config.dart`

```dart
class AppConfig {
  static String apiBaseUrl = 'http://<你的域名>';

  static List<String> backupUrls = [
    'http://<你的域名>',
    'http://192.168.30.106:5000',  // 内网备用
  ];
}
```

---

## 常见问题

### 1. DNS 解析不到 IPv6 地址

- 检查 DDNS-go 是否正常运行
- 检查域名服务商 API 密钥是否正确
- 确认已添加 AAAA 记录

### 2. 移动端连接超时

- 确认手机使用的是移动网络（支持 IPv6）
- 测试域名是否能访问：`ping6 <你的域名>`
- 检查服务器防火墙是否开放 80/443 端口

### 3. IPv6 地址变化

DDNS-go 会自动检测并更新，无需手动操作。

---

## 完整配置检查清单

- [ ] DDNS-go 服务运行正常
- [ ] DNS AAAA 记录已添加（主机记录：www）
- [ ] DNS 解析返回正确的 IPv6 地址
- [ ] 服务器防火墙开放 80/443 端口（IPv6）
- [ ] 移动端服务器地址配置正确
- [ ] App 能正常登录

---

## 配置 SSL 证书（可选）

有证书后，修改 `nginx.conf` 启用 HTTPS：

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name <你的域名>;

    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    # ...
}
```

然后移动端使用：`https://<你的域名>`
