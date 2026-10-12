# 版本检测 URL（仅支持HTTPS）
# 拆分后 updates/version.json 统一存放在 desktop 仓库根目录
VERSION_URLS = [
    "https://raw.githubusercontent.com/XTLT/db-population-system-desktop/master/updates/version.json",
]

# 更新源白名单域名
ALLOWED_DOMAINS = [
    "github.com",
    "githubusercontent.com",
]

# 是否启用自动更新（默认禁用，需手动确认）
AUTO_UPDATE_ENABLED = False

# 是否强制要求签名验证
REQUIRE_SIGNATURE = True

# 是否强制要求GPG签名验证
REQUIRE_GPG_SIGNATURE = False  # 可选，如果提供则验证

# GPG公钥指纹白名单（发布者的GPG密钥指纹）
GPG_KEY_FINGERPRINTS = [
    # 示例：添加发布者的GPG密钥指纹
    # "ABC123DEF456...",
]

# Windows代码签名证书指纹白名单
CODE_SIGNING_CERTS = [
    # 示例：添加发布者的代码签名证书指纹
    # "XYZ789...",
]
