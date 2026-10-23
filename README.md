# 人口通 - 服务端

人口通系统的服务端仓库：Flask API + SQLite 数据库 + Web 前端（`web_static/`）+ desktop/mobile 客户端更新发布。

> 本仓库由原 `db-population-system` 拆分而来；桌面端在 `db-population-system-desktop`，移动端在 `db-population-system-mobile`。

## 技术栈

- Python 3.10+ / Flask / SQLAlchemy / SQLite
- Gunicorn（生产 WSGI）+ systemd 开机自启
- stunnel mTLS 双向证书加密（HTTPS，IPv4 + IPv6 双栈，公网可直连）
- Web 前端为纯静态页面（由服务端直接托管）

## 一键安装（推荐，不懂技术也能装）

`install.sh` 会自动检测并安装全部所需环境与依赖、生成证书、配置 systemd 开机自启，并自动验证安装结果。**用户只需运行一条命令，其余全自动**。

```bash
cd server
sudo bash install.sh -y                # 默认 HTTPS 端口 5000
# 自定义端口 / 域名：
sudo bash install.sh -p 5000 -d tension02.ren -y
```

| 参数 | 说明 |
|---|---|
| `-p <端口>` | 对外 HTTPS 端口（默认 5000） |
| `-d <域名>` | 客户端访问域名，多个用英文逗号分隔（自动加入证书） |
| `-w <数量>` | gunicorn 进程数（默认 2，一般不用改） |
| `-n <名称>` | systemd 服务名前缀（默认 population，一般不用改） |
| `-y` | 全自动，不询问任何确认 |

安装完成后：

- 服务开机自启：`systemctl status population-server`
- 浏览器访问 `https://服务器IP:5000` 即 Web 管理端
- desktop / mobile 客户端填 `https://服务器IP:5000` 即可连接

## 手动安装

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 cert_manager.py            # 首次生成自签名证书（10 年有效期）
sudo bash deploy.sh install        # 部署为 systemd 服务
```

开发模式调试：`python3 app_modular.py`（默认端口 5000）。

## 升级与运维

```bash
sudo bash upgrade.sh               # 升级向导（更新代码 + 重启服务）
sudo systemctl status|restart|stop population-server   # 服务管理
./start_server.sh                  # 手动启动
sudo bash uninstall.sh             # 卸载
```

## 客户端更新发布

服务端同时是 desktop / mobile 的**更新主源**（客户端检查更新直接从服务器下载）：

```bash
# 发布桌面端（说明文字不要含空格，用 ASCII）
bash scripts/publish_update.sh desktop /tmp/update_desktop_v0034.exe 0.0.34 34 "v0.0.34:relation-dropdown-standard"

# 发布移动端
bash scripts/publish_update.sh mobile /tmp/update_mobile_v0027.apk 0.0.27 27 "v0.0.27:relation-dropdown-standard"
```

发布脚本自动写入 `version.json`（含版本号、文件、SHA256 校验值），客户端下载时强制校验 SHA256。

## 主要接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/login | 登录（含失败限流） |
| GET | /api/persons | 人员列表（筛选/搜索） |
| GET | /api/family/<户号> | 家庭成员 |
| POST | /api/person | 添加人员（每户唯一户主校验） |
| PUT | /api/person/<id> | 修改人员（换户主自动整户关系重建） |
| POST | /api/import_export/import | 导入 Excel |
| GET | /api/update/check | 客户端更新检查 |
| GET | /api/update/download | 客户端更新包下载 |

详见 `docs/模块化架构说明.md`。

## 目录结构

```
install.sh               # 一键傻瓜安装脚本
deploy.sh                # 部署 / 升级脚本
upgrade.sh               # 升级向导
start_server.sh          # 手动启动脚本
app_modular.py           # Flask 应用入口（蓝图注册）
api/                     # 业务蓝图，每蓝图一包（一函数一文件）
database/                # 数据库层：模型 + 迁移 + 会话
excel_importer/          # Excel 导入器
web_static/              # Web 前端（index.html + js/）
utils/                   # 安全、响应、公共工具
scripts/                 # 更新发布、证书轮换等运维脚本
deploy/                  # systemd 服务文件
docs/                    # 部署 / 运维 / 安全文档
```

## 默认管理员

首次启动数据库为空时自动创建 `admin / admin123`，登录后必须创建正式管理员账户，默认账户随即自动禁用。

## 数据库

- 默认位置：`server/population.db`（gitignore，不入库）
- 自动迁移：启动时幂等补列，无需手工操作
- 备份：`backups/` 目录（自动 + 手动）
