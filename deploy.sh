#!/bin/bash

# ============================================
# 人口通 - 一键部署/升级脚本
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$PROJECT_DIR/server"
DATA_DIR="$PROJECT_DIR/data"
VENV_DIR="$SERVER_DIR/venv"

# 打印函数
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}  $1${NC}"
}

# 检查Python版本
check_python() {
    print_header "检查 Python 环境"
    
    # 优先使用 python3
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "未找到 Python，请先安装 Python 3.10+"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "Python 版本: $PYTHON_VERSION"
    
    # 检查版本是否 >= 3.10
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        print_error "Python 版本过低，需要 3.10 或更高版本"
        exit 1
    fi
    
    print_success "Python 环境检查通过"
}

# 创建虚拟环境
create_venv() {
    print_header "创建虚拟环境"
    
    if [ -d "$VENV_DIR" ]; then
        print_info "虚拟环境已存在: $VENV_DIR"
        read -p "是否重新创建？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "跳过虚拟环境创建"
            return
        fi
        print_info "删除旧虚拟环境..."
        rm -rf "$VENV_DIR"
    fi
    
    print_info "创建虚拟环境: $VENV_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR"
    print_success "虚拟环境创建成功"
}

# 安装依赖
install_deps() {
    print_header "安装依赖包"
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip -q
    
    # 安装依赖
    print_info "安装项目依赖..."
    if [ -f "$SERVER_DIR/requirements.txt" ]; then
        pip install -r "$SERVER_DIR/requirements.txt" -q
        print_success "依赖安装成功"
    else
        print_error "未找到 requirements.txt"
        exit 1
    fi
    
    # 验证关键包
    print_info "验证关键依赖..."
    python -c "import flask; print(f'  Flask {flask.__version__}')" || print_error "Flask 安装失败"
    python -c "import sqlalchemy; print(f'  SQLAlchemy {sqlalchemy.__version__}')" || print_error "SQLAlchemy 安装失败"
    python -c "import openpyxl; print(f'  openpyxl {openpyxl.__version__}')" || print_error "openpyxl 安装失败"
}

# 创建目录结构
create_dirs() {
    print_header "创建目录结构"
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/Photos"
    mkdir -p "$DATA_DIR/backups"
    mkdir -p "$DATA_DIR/certs"
    mkdir -p "$DATA_DIR/logs"
    mkdir -p "$DATA_DIR/reports"
    
    print_success "目录结构创建完成"
    print_info "数据目录: $DATA_DIR"
}

# 创建配置文件
create_config() {
    print_header "创建配置文件"
    
    CONFIG_FILE="$PROJECT_DIR/config.yaml"
    CONFIG_EXAMPLE="$PROJECT_DIR/config.example.yaml"
    
    if [ -f "$CONFIG_FILE" ]; then
        print_info "配置文件已存在: $CONFIG_FILE"
        return
    fi
    
    if [ -f "$CONFIG_EXAMPLE" ]; then
        cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
        print_success "已从模板创建配置文件: $CONFIG_FILE"
        print_warning "请根据实际情况修改配置文件"
    else
        print_warning "未找到配置模板，请手动创建 config.yaml"
    fi
}

# 生成SSL证书
generate_ssl() {
    print_header "生成 SSL 证书"
    
    CERT_FILE="$DATA_DIR/certs/server.crt"
    KEY_FILE="$DATA_DIR/certs/server.key"
    
    if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        print_info "SSL 证书已存在"
        return
    fi
    
    print_info "生成自签名证书..."
    openssl req -x509 -newkey rsa:2048 -keyout "$KEY_FILE" -out "$CERT_FILE" \
        -days 365 -nodes -subj "/CN=localhost" 2>/dev/null
    
    print_success "SSL 证书生成成功"
    print_info "证书位置: $CERT_FILE"
    print_warning "自签名证书仅用于开发测试，生产环境请使用正式证书"
}

# 初始化数据库
init_database() {
    print_header "初始化数据库"
    
    DB_FILE="$DATA_DIR/population.db"
    
    if [ -f "$DB_FILE" ]; then
        print_info "数据库已存在: $DB_FILE"
        return
    fi
    
    print_info "数据库将在首次启动时自动创建"
}

# 验证安装
verify_install() {
    print_header "验证安装"
    
    source "$VENV_DIR/bin/activate"
    
    # 检查模块导入
    print_info "检查模块导入..."
    python -c "
import sys
sys.path.insert(0, '$SERVER_DIR')
from database import get_session, Person
from utils.security import hash_password
from config import BASE_DIR
print('  所有模块导入成功')
"
    
    # 运行测试脚本
    if [ -f "$SERVER_DIR/test_modules.py" ]; then
        print_info "运行模块验证..."
        cd "$SERVER_DIR" && python test_modules.py
    fi
    
    print_success "安装验证通过"
}

# 显示启动命令
show_start_info() {
    print_header "部署完成"
    
    echo -e "${GREEN}服务端启动命令:${NC}"
    echo ""
    echo "  cd $PROJECT_DIR"
    echo "  ./start_server.sh"
    echo ""
    echo -e "${GREEN}或手动启动:${NC}"
    echo ""
    echo "  cd $SERVER_DIR"
    echo "  source venv/bin/activate"
    echo "  python web_app.py"
    echo ""
    echo -e "${YELLOW}首次登录信息:${NC}"
    echo "  用户名: admin"
    echo "  密码: amdin123"
    echo -e "${YELLOW}  请在生产环境中立即修改密码!${NC}"
    echo ""
}

# 完整安装
full_install() {
    print_header "开始完整部署"
    
    check_python
    create_venv
    install_deps
    create_dirs
    create_config
    generate_ssl
    init_database
    verify_install
    show_start_info
}

# 升级
upgrade() {
    print_header "开始升级"
    
    # 检查虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        print_error "虚拟环境不存在，请先运行 ./deploy.sh install"
        exit 1
    fi
    
    # 备份数据库
    print_info "备份数据库..."
    BACKUP_FILE="$DATA_DIR/backups/pre_upgrade_$(date +%Y%m%d_%H%M%S).db"
    if [ -f "$DATA_DIR/population.db" ]; then
        cp "$DATA_DIR/population.db" "$BACKUP_FILE"
        print_success "数据库已备份: $BACKUP_FILE"
    fi
    
    # 激活虚拟环境并升级依赖
    source "$VENV_DIR/bin/activate"
    
    print_info "升级 pip..."
    pip install --upgrade pip -q
    
    print_info "升级依赖包..."
    pip install -r "$SERVER_DIR/requirements.txt" --upgrade -q
    
    print_success "依赖升级完成"
    
    # 验证
    verify_install
    
    print_header "升级完成"
    print_info "请重启服务: ./start_server.sh restart"
}

# 仅安装依赖
install_only() {
    check_python
    
    if [ ! -d "$VENV_DIR" ]; then
        create_venv
    fi
    
    install_deps
    print_success "依赖安装完成"
}

# 显示帮助
show_help() {
    echo ""
    echo "用法: ./deploy.sh [命令]"
    echo ""
    echo "命令:"
    echo "  install    完整安装（推荐首次使用）"
    echo "  upgrade    升级系统（更新代码后执行）"
    echo "  deps       仅安装/更新依赖"
    echo "  verify     验证安装"
    echo "  help       显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh install    # 首次部署"
    echo "  ./deploy.sh upgrade    # 升级系统"
    echo ""
}

# 主入口
case "$1" in
    install|"")
        full_install
        ;;
    upgrade)
        upgrade
        ;;
    deps)
        install_only
        ;;
    verify)
        verify_install
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
