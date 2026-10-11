#!/bin/bash
# ========================================
# 人口通 - 服务端一键安装
# ========================================
# 仅安装服务端（Flask + SQLite + Web 前端 + systemd 开机启动）
# 桌面端/移动端请分别使用 db-population-system-desktop / -mobile 仓库的脚本

set -e

echo "========================================"
echo "   人口通 - 服务端一键安装"
echo "========================================"

# 检测系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "[INFO] 检测到系统: $PRETTY_NAME"
fi

# 1. 检查网络
echo "[STEP] 检查网络连接..."
if curl -s --connect-timeout 5 -o /dev/null https://pypi.org; then
    echo "[INFO] 网络连接正常"
else
    echo "[WARN] 无法访问 pypi.org，可能网络受限，继续尝试..."
fi

# 2. 系统依赖
echo "[STEP] 检查并安装系统依赖..."
if command -v apt-get >/dev/null 2>&1; then
    echo "[INFO] 更新软件源..."
    apt-get update -qq || true
    echo "[INFO] 安装系统依赖..."
    apt-get install -y -qq python3-dev libffi-dev libargon2-0 sqlite3 net-tools openssl >/dev/null 2>&1 || true
fi
echo "[INFO] 系统依赖安装完成"

# 3. Python 环境
echo "[STEP] 检查 Python 环境..."
python3 --version
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] 未找到 Python3"
    exit 1
fi

# 4. 目录结构
echo "[STEP] 创建目录结构..."
mkdir -p data/certs data/logs data/backups data/Photos data/uploads
chmod +x start_server.sh 2>/dev/null || true

# 5. 服务端依赖
echo "[STEP] 安装服务端依赖..."
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[INFO] 服务端依赖安装完成"

# 6. SSL 证书
echo "[STEP] 生成 SSL 自签名证书（10年有效期）..."
if [ ! -f data/certs/server.crt ]; then
    python3 cert_manager.py || true
    # 兜底：直接用 openssl 生成
    if [ ! -f data/certs/server.crt ]; then
        mkdir -p data/certs
        openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
            -keyout data/certs/server.key -out data/certs/server.crt \
            -subj "/CN=population-server" 2>/dev/null
    fi
fi
echo "[INFO] SSL 证书已生成"

# 7. 端口检查
echo "[STEP] 检查端口 5000..."
if ss -tlnp 2>/dev/null | grep -q ':5000'; then
    echo "[WARN] 端口 5000 已被占用，请先停止占用端口的服务"
fi

# 8. systemd 开机启动
echo "[STEP] 配置开机启动服务..."
if command -v systemctl >/dev/null 2>&1; then
    mkdir -p /etc/systemd/system
    cp deploy/population-server.service /etc/systemd/system/population-server.service
    # 修正工作目录
    sed -i "s|WorkingDirectory=.*|WorkingDirectory=$(pwd)|g" /etc/systemd/system/population-server.service
    sed -i "s|ExecStart=.*|ExecStart=$(pwd)/venv/bin/gunicorn -w 3 -b [::]:5000 --certfile=$(pwd)/data/certs/server.crt --keyfile=$(pwd)/data/certs/server.key app_modular:app|g" /etc/systemd/system/population-server.service
    systemctl daemon-reload
    systemctl enable population-server
    systemctl start population-server
    echo "[INFO] 服务已启动: population-server"
else
    echo "[WARN] 未检测到 systemd，请手动启动: ./start_server.sh"
fi

echo "========================================"
echo "   安装完成！"
echo "========================================"
echo "服务管理命令："
echo "   sudo systemctl start|stop|status population-server"
echo "Web 访问："
echo "   https://服务器IP:5000"
echo "默认管理员：admin / admin123（首次登录后必须创建正式管理员）"
echo "⚠️  生产环境请立即修改默认密码！"
