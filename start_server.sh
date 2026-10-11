#!/bin/bash
# ========================================
# 人口通 - 服务端启动脚本
# 支持内网和IPv6双域名访问
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="${SCRIPT_DIR}/server"
DATA_DIR="${SCRIPT_DIR}/data"
LOG_DIR="${DATA_DIR}/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建必要目录
create_directories() {
    mkdir -p "${DATA_DIR}"
    mkdir -p "${DATA_DIR}/Photos"
    mkdir -p "${DATA_DIR}/backups"
    mkdir -p "${DATA_DIR}/logs"
    mkdir -p "${DATA_DIR}/certs"
    mkdir -p "${DATA_DIR}/reports"
    echo_info "目录结构已创建"
}

# 检查 Python 环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo_error "未找到 Python3，请先安装 Python3"
        exit 1
    fi
    echo_info "Python3 已安装: $(python3 --version)"
}

# 安装依赖
install_dependencies() {
    echo_info "安装服务端依赖..."
    cd "${SERVER_DIR}"
    
    if [ ! -d "venv" ]; then
        echo_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo_info "依赖安装完成"
}

# 配置检查
check_config() {
    if [ ! -f "${SERVER_DIR}/config.yaml" ]; then
        echo_warn "配置文件不存在，使用示例配置..."
        if [ -f "${SCRIPT_DIR}/config.example.yaml" ]; then
            cp "${SCRIPT_DIR}/config.example.yaml" "${SERVER_DIR}/config.yaml"
        fi
    fi
    echo_info "配置文件已就绪"
}

# 启动服务器
start_server() {
    local PORT=${1:-5000}
    local MODE=${2:-"production"}
    
    cd "${SERVER_DIR}"
    
    if [ ! -d "venv" ]; then
        install_dependencies
    fi
    
    source venv/bin/activate
    
    echo_info "启动服务器..."
    echo ""
    echo "========================================"
    echo "   人口通 - 服务端"
    echo "========================================"
    echo "  访问地址:"
    echo "    内网: https://<内网IP>:${PORT}"
    echo "    IPv6: https://[<IPv6地址>]:${PORT}"
    echo "========================================"
    echo ""
    
    if [ "$MODE" = "development" ]; then
        FLASK_DEBUG=1 python3 app_modular.py
    else
        # 生产模式使用 gunicorn
        # 使用 ${PORT:-5000} 确保即使 PORT 为空也有默认值
        local GUNICORN_PORT="${PORT:-5000}"
        if command -v gunicorn &> /dev/null; then
            gunicorn -w 3 -b "[::]:${GUNICORN_PORT}" --certfile="${DATA_DIR}/certs/server.crt" --keyfile="${DATA_DIR}/certs/server.key" app_modular:app
        else
            python3 app_modular.py
        fi
    fi
}

# 停止服务器
stop_server() {
    echo_info "停止服务器..."
    pkill -f "app_modular.py" || true
    pkill -f "gunicorn.*population" || true
    echo_info "服务器已停止"
}

# 查看状态
status() {
    echo_info "服务状态:"
    if pgrep -f "app_modular.py" > /dev/null; then
        echo_info "服务器正在运行"
        pgrep -f "app_modular.py"
    else
        echo_warn "服务器未运行"
    fi
}

# 备份数据
backup_data() {
    local BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    local BACKUP_PATH="${DATA_DIR}/backups/${BACKUP_NAME}"
    
    mkdir -p "${BACKUP_PATH}"
    
    # 备份数据库
    if [ -f "${DATA_DIR}/population.db" ]; then
        cp "${DATA_DIR}/population.db" "${BACKUP_PATH}/"
        echo_info "数据库已备份到: ${BACKUP_PATH}"
    fi
    
    # 备份照片
    if [ -d "${DATA_DIR}/Photos" ]; then
        cp -r "${DATA_DIR}/Photos" "${BACKUP_PATH}/"
        echo_info "照片已备份到: ${BACKUP_PATH}"
    fi
}

# 使用帮助
show_help() {
    echo "人口通 - 服务端管理脚本"
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  start [port] [mode]  启动服务器 (默认端口:5000, 模式:production)"
    echo "  stop                 停止服务器"
    echo "  restart              重启服务器"
    echo "  status               查看状态"
    echo "  install              安装依赖"
    echo "  backup               备份数据"
    echo "  help                 显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 start 5000 production"
    echo "  $0 start 8080 development"
    echo "  $0 backup"
}

# 主入口
case "${1:-help}" in
    start)
        create_directories
        check_config
        start_server "${2:-5000}" "${3:-production}"
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        create_directories
        start_server "${2:-5000}" "${3:-production}"
        ;;
    status)
        status
        ;;
    install)
        check_python
        create_directories
        install_dependencies
        ;;
    backup)
        backup_data
        ;;
    help|*)
        show_help
        ;;
esac
