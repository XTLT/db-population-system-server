#!/bin/bash

# ============================================
# 人口通 - 快速升级脚本
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$PROJECT_DIR/server"
VENV_DIR="$SERVER_DIR/venv"
DATA_DIR="$PROJECT_DIR/data"

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}人口通 - 升级向导${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}虚拟环境不存在，请先运行: ./deploy.sh install${NC}"
    exit 1
fi

# 备份数据库
echo -e "${GREEN}[1/4] 备份数据库...${NC}"
if [ -f "$DATA_DIR/population.db" ]; then
    BACKUP_FILE="$DATA_DIR/backups/backup_$(date +%Y%m%d_%H%M%S).db"
    mkdir -p "$DATA_DIR/backups"
    cp "$DATA_DIR/population.db" "$BACKUP_FILE"
    echo "  ✓ 已备份到: $BACKUP_FILE"
else
    echo "  - 数据库不存在，跳过备份"
fi

# 激活虚拟环境
echo -e "${GREEN}[2/4] 激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate"

# 升级依赖
echo -e "${GREEN}[3/4] 升级依赖包...${NC}"
pip install --upgrade pip -q
pip install -r "$SERVER_DIR/requirements.txt" --upgrade -q
echo "  ✓ 依赖升级完成"

# 验证安装
echo -e "${GREEN}[4/4] 验证安装...${NC}"
python -c "
import sys
sys.path.insert(0, '$SERVER_DIR')
from database import get_session
from utils.security import hash_password
from config import BASE_DIR
print('  ✓ 模块验证通过')
"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}升级完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "请重启服务:"
echo "  ./start_server.sh restart"
echo ""
