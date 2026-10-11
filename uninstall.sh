#!/bin/bash
# ========================================
# 人口通 - 一键卸载脚本
# 警告: 此脚本将删除所有服务器数据和配置
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="${SCRIPT_DIR}/server"
DESKTOP_DIR="${SCRIPT_DIR}/desktop"
DATA_DIR="${SCRIPT_DIR}/data"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 显示警告
show_warning() {
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}   ⚠️  警告: 数据将被永久删除!  ⚠️${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "此脚本将删除以下内容:"
    echo ""
    echo "  1. 服务端虚拟环境 (server/venv/)"
    echo "  2. 桌面端虚拟环境 (desktop/venv/)"
    echo "  3. 数据库文件 (data/population.db)"
    echo "  4. 照片存储 (data/Photos/)"
    echo "  5. 备份文件 (data/backups/)"
    echo "  6. SSL证书 (data/certs/)"
    echo "  7. 日志文件 (data/logs/)"
    echo "  8. 报告文件 (data/reports/)"
    echo "  9. 配置文件 (server/config.yaml)"
    echo " 10. ddns-go 服务 (如果已安装)"
    echo ""
    echo -e "${YELLOW}这些操作不可逆！数据将无法恢复！${NC}"
    echo ""
}

# 确认卸载
confirm_uninstall() {
    show_warning
    
    read -p "确定要继续卸载吗? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo_info "卸载已取消"
        exit 0
    fi
    
    read -p "再次确认: 输入 'uninstall' 继续: " confirm2
    if [ "$confirm2" != "uninstall" ]; then
        echo_info "卸载已取消"
        exit 0
    fi
}

# 停止服务器
stop_server() {
    echo_step "停止服务器..."
    
    # 尝试通过 start_server.sh 停止
    if [ -f "${SCRIPT_DIR}/start_server.sh" ]; then
        cd "${SCRIPT_DIR}"
        ./start_server.sh stop 2>/dev/null || true
    fi
    
    # 查找并杀死相关进程
    local pids=$(pgrep -f "python.*web_app.py|python.*app_modular.py|gunicorn.*population" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo_info "找到运行中的服务器进程: $pids"
        kill $pids 2>/dev/null || true
        sleep 2
        # 强制杀死残留进程
        kill -9 $pids 2>/dev/null || true
        echo_info "服务器进程已停止"
    else
        echo_info "没有发现运行中的服务器进程"
    fi
}

# 卸载 ddns-go
uninstall_ddns_go() {
    echo_step "卸载 ddns-go 服务..."
    
    if command -v systemctl &> /dev/null; then
        if systemctl is-active ddns-go &> /dev/null; then
            sudo systemctl stop ddns-go 2>/dev/null || true
            echo_info "ddns-go 服务已停止"
        fi
        
        if systemctl is-enabled ddns-go &> /dev/null; then
            sudo systemctl disable ddns-go 2>/dev/null || true
            echo_info "ddns-go 已禁用开机自启"
        fi
        
        if [ -f /etc/systemd/system/ddns-go.service ]; then
            sudo rm -f /etc/systemd/system/ddns-go.service
            sudo systemctl daemon-reload
            echo_info "ddns-go 服务文件已删除"
        fi
    fi
    
    # 删除 ddns-go 二进制文件
    if [ -f /usr/local/bin/ddns-go ]; then
        sudo rm -f /usr/local/bin/ddns-go
        echo_info "ddns-go 二进制文件已删除"
    fi
    
    echo_info "ddns-go 卸载完成"
}

# 删除虚拟环境
remove_virtual_environments() {
    echo_step "删除虚拟环境..."
    
    # 服务端虚拟环境
    if [ -d "${SERVER_DIR}/venv" ]; then
        rm -rf "${SERVER_DIR}/venv"
        echo_info "已删除 server/venv/"
    fi
    
    # 桌面端虚拟环境
    if [ -d "${DESKTOP_DIR}/venv" ]; then
        rm -rf "${DESKTOP_DIR}/venv"
        echo_info "已删除 desktop/venv/"
    fi
}

# 删除数据目录
remove_data_directory() {
    echo_step "删除数据目录..."
    
    if [ -d "${DATA_DIR}" ]; then
        echo_warn "即将删除数据目录: ${DATA_DIR}"
        echo_warn "包含: 数据库、照片、备份、证书、日志等"
        
        read -p "是否保留备份文件? (y/n): " keep_backup
        if [ "$keep_backup" = "y" ] && [ -d "${DATA_DIR}/backups" ]; then
            # 创建临时备份
            local backup_temp="/tmp/population_backup_$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$backup_temp"
            cp -r "${DATA_DIR}/backups"/* "$backup_temp/" 2>/dev/null || true
            echo_info "备份文件已保存到: $backup_temp"
        fi
        
        rm -rf "${DATA_DIR}"
        echo_info "数据目录已删除"
    else
        echo_info "数据目录不存在"
    fi
}

# 删除配置文件
remove_config_files() {
    echo_step "删除配置文件..."
    
    # 服务端配置
    if [ -f "${SERVER_DIR}/config.yaml" ]; then
        rm -f "${SERVER_DIR}/config.yaml"
        echo_info "已删除 server/config.yaml"
    fi
    
    # 删除 __pycache__ 目录
    find "${SERVER_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${DESKTOP_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo_info "已清理 Python 缓存文件"
    
    # 删除 .pyc 文件
    find "${SERVER_DIR}" -name "*.pyc" -delete 2>/dev/null || true
    find "${DESKTOP_DIR}" -name "*.pyc" -delete 2>/dev/null || true
}

# 可选: 删除整个项目
remove_project() {
    echo ""
    read -p "是否删除整个项目目录? (y/n): " remove_all
    if [ "$remove_all" = "y" ]; then
        echo_warn "即将删除整个项目: ${SCRIPT_DIR}"
        read -p "最后确认 - 输入 'DELETE' 继续: " final_confirm
        if [ "$final_confirm" = "DELETE" ]; then
            cd /
            rm -rf "${SCRIPT_DIR}"
            echo_info "项目目录已完全删除"
            echo_info "卸载完成!"
            exit 0
        fi
    fi
    echo_info "保留项目目录"
}

# 显示完成信息
show_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   ✓ 卸载完成!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "已删除:"
    echo "  ✓ 服务端虚拟环境"
    echo "  ✓ 桌面端虚拟环境"
    echo "  ✓ 数据库和照片"
    echo "  ✓ SSL证书"
    echo "  ✓ 配置文件"
    echo "  ✓ 日志文件"
    echo ""
    if [ "$keep_backup" = "y" ]; then
        echo "备份文件已保存到: /tmp/population_backup_*"
    fi
    echo ""
    echo "如需重新安装，请运行:"
    echo "  ./install.sh"
    echo ""
}

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help, -h       显示帮助信息"
    echo "  --force, -f      跳过确认（危险）"
    echo "  --keep-data      保留数据目录"
    echo "  --keep-venv      保留虚拟环境"
    echo "  --ddns-only      仅卸载 ddns-go"
    echo ""
    echo "示例:"
    echo "  $0               交互式卸载"
    echo "  $0 --keep-data   卸载但保留数据"
    echo "  $0 --ddns-only   仅卸载 ddns-go 服务"
    echo ""
}

# 主函数
main() {
    local force=false
    local keep_data=false
    local keep_venv=false
    local ddns_only=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --force|-f)
                force=true
                shift
                ;;
            --keep-data)
                keep_data=true
                shift
                ;;
            --keep-venv)
                keep_venv=true
                shift
                ;;
            --ddns-only)
                ddns_only=true
                shift
                ;;
            *)
                echo_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo ""
    echo "========================================"
    echo "   人口通 - 一键卸载"
    echo "========================================"
    echo ""
    
    # 仅卸载 ddns-go
    if [ "$ddns_only" = true ]; then
        uninstall_ddns_go
        echo_info "ddns-go 卸载完成"
        exit 0
    fi
    
    # 确认卸载
    if [ "$force" = false ]; then
        confirm_uninstall
    else
        echo_warn "使用 --force 参数，跳过确认"
    fi
    
    # 停止服务器
    stop_server
    
    # 卸载 ddns-go
    uninstall_ddns_go
    
    # 删除虚拟环境
    if [ "$keep_venv" = false ]; then
        remove_virtual_environments
    else
        echo_info "保留虚拟环境"
    fi
    
    # 删除数据目录
    if [ "$keep_data" = false ]; then
        remove_data_directory
    else
        echo_info "保留数据目录"
    fi
    
    # 删除配置文件
    remove_config_files
    
    # 可选: 删除整个项目
    if [ "$force" = false ]; then
        remove_project
    fi
    
    # 显示完成信息
    show_completion
}

# 执行主函数
main "$@"
