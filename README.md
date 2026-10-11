# 人口通 - 服务端

人口通系统的服务端仓库，包含 Flask API + SQLite 数据库 + Web 前端（`web_static/`）。

> 本仓库由原 `db-population-system` 拆分而来，仅包含服务端与 Web 前端；桌面端、移动端分别在 `db-population-system-desktop`、`db-population-system-mobile` 仓库。

## 技术栈

- Python 3.10+ / Flask / SQLAlchemy / SQLite
- 自签名 SSL 证书（10 年有效期，首次启动自动生成）
- Web 前端为纯静态页面（`web_static/`，由服务端直接托管）

## 快速开始

```bash
# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 生成证书并启动（HTTP 建议仅内网调试，正式使用走 HTTPS）
python3 cert_manager.py   # 生成自签名证书（已有证书则跳过）
python3 app_modular.py    # 开发模式启动，默认端口 5000
```

生产环境一键安装（Ubuntu/Debian）：

```bash
sudo ./install.sh
```

启动后浏览器访问 `https://服务器IP:5000`。

## 目录结构

```
app_modular.py           # Flask 应用入口（蓝图注册）
api/                     # 18 个业务蓝图，每蓝图一包（一函数一文件）
database/                # 数据库层：模型 + 迁移 + 会话
excel_importer/          # Excel 导入器（人员/补贴/学生等）
excel_payment_templates/ # 补贴导入模板生成
web_static/              # Web 前端（index.html + js/）
utils/                   # 安全、响应、公共工具
deploy/                  # systemd 服务文件
docs/                    # 部署/运维/安全文档
```

## 服务管理（systemd）

```bash
sudo systemctl start|stop|status population-server
```

## 默认管理员

首次启动数据库为空时自动创建 `admin / admin123`，登录后必须创建正式管理员账户，默认账户随即禁用。

## 主要接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/login | 登录 |
| GET | /api/persons | 人员列表（支持筛选/搜索） |
| POST | /api/import_export/import | 导入 Excel |
| GET | /api/land_subsidy | 地力补贴列表 |
| GET | /api/statistics | 数据统计 |
| ... | ... | 详见 docs/模块化架构说明.md |

## 数据库

- 默认位置：`server/population.db`（与仓库 `data/` 目录平级，被 gitignore）
- 自动迁移：启动时 `_migrate_db` 幂等补列，无需手工操作
- 备份：`data/backups/`（每日自动 + 手动）
