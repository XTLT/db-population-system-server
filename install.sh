#!/bin/bash
# ============================================================
# 人口通 - 服务端 一键傻瓜安装脚本
# ------------------------------------------------------------
# 只需要运行这一条命令，脚本会自动检测并安装全部所需环境、
# 依赖、证书、开机自启服务，并自动验证安装是否成功。
# 无需任何其它操作，不懂技术也能装成功。
#
# 用法（在 server 代码目录内执行）:
#     sudo bash install.sh -y
#
# 可选参数:
#     -p <端口>    对外 HTTPS 端口（默认 5000）
#     -d <域名>    客户端访问域名，多个用英文逗号分隔（自动加入证书）
#     -w <数量>    gunicorn 进程数（默认 2，一般不用改）
#     -n <名称>    服务名前缀（默认 population，一般不用改）
#     -y           全自动，不询问任何确认
#
# 示例:
#     sudo bash install.sh -y
#     sudo bash install.sh -p 5000 -d tension02.ren -y
# ============================================================
set -euo pipefail

PORT="${PORT:-5000}"
WORKERS="${WORKERS:-2}"
DOMAINS=""
SVC_PREFIX="population"
SKIP_CONFIRM=0
while [ $# -gt 0 ]; do
    case "$1" in
        -p) PORT="$2"; shift 2 ;;
        -d) DOMAINS="$2"; shift 2 ;;
        -w) WORKERS="$2"; shift 2 ;;
        -n) SVC_PREFIX="$2"; shift 2 ;;
        -y) SKIP_CONFIRM=1; shift ;;
        *) echo "未知参数: $1（用法见脚本头部注释）" >&2; exit 1 ;;
    esac
done

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
INNER_PORT=$((PORT + 1))
CERT_DIR="$INSTALL_DIR/certs"

# ---- 输出函数 ----
red()    { printf "\033[31m%s\033[0m\n" "$*"; }
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
log()    { printf "\033[36m[%s] %s\033[0m\n" "$(date +%H:%M:%S)" "$*"; }
step()   { echo ""; echo "===== $* ====="; }

trap 'echo ""; red "安装失败！请把上面的错误信息发给维护者。"; exit 1' ERR

# ---- 横幅 ----
echo "======================================================"
echo "         人口通 - 服务端 一键安装"
echo "======================================================"
echo "  安装目录: $INSTALL_DIR"
echo "  对外端口: $PORT（HTTPS，IPv4+IPv6 双栈）"
[ -n "$DOMAINS" ] && echo "  域名: $DOMAINS"
echo ""

# ---- 0. root 权限（自动 sudo 重跑）----
if [ "$(id -u)" -ne 0 ]; then
    echo "需要 root 权限，自动使用 sudo 重新执行..."
    exec sudo bash "$0" "$@"
fi

# ---- 1. 系统检测 ----
step "检测系统环境"
if ! command -v apt-get >/dev/null 2>&1; then
    red "仅支持 Debian / Ubuntu / Armbian 等 apt 系统，当前系统无法自动安装。"
    exit 1
fi
if [ -f /etc/os-release ]; then
    PRETTY_NAME="$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | tr -d '"')"
    log "系统: ${PRETTY_NAME:-未知}"
fi
[ "$SKIP_CONFIRM" -ne 1 ] || log "全自动模式（-y），跳过确认"

# ---- 2. 确认 ----
if [ "$SKIP_CONFIRM" -ne 1 ]; then
    echo ""
    echo "即将在以下目录安装人口通服务端：$INSTALL_DIR"
    read -r -p "确认继续? (y/N) " ans
    case "$ans" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

# ---- 3. 系统依赖 ----
step "安装系统依赖（首次约 1-3 分钟）"
apt-get update -qq >/dev/null 2>&1 || log "软件源更新失败（网络问题？），继续尝试安装"
apt-get install -y -qq \
    python3 python3-venv python3-pip openssl sqlite3 curl net-tools \
    libargon2-1 libargon2-dev libffi-dev >/dev/null 2>&1 \
  || apt-get install -y \
    python3 python3-venv python3-pip openssl sqlite3 curl net-tools \
    libargon2-1 libargon2-dev libffi-dev >/dev/null
if ! command -v stunnel >/dev/null 2>&1; then
    log "安装 stunnel..."
    apt-get install -y stunnel >/dev/null 2>&1 \
        || apt-get install -y stunnel4 >/dev/null \
        || { red "stunnel 安装失败，请检查网络后重试"; exit 1; }
fi
STUNNEL_BIN="$(command -v stunnel)"
log "系统依赖安装完成（stunnel: $STUNNEL_BIN）"

# ---- 4. 目录结构 ----
step "创建数据目录"
mkdir -p "$CERT_DIR" logs backups Photos reports uploads
log "数据目录创建完成"

# ---- 5. Python 虚拟环境与依赖 ----
step "安装服务端 Python 依赖（首次约 3-8 分钟）"
# ARM 平台（树莓派/OneCloud/盒子等）无 pandas 等 wheel，源码编译极慢（可达 1 小时）；
# 先用 apt 装二进制包 + venv --system-site-packages，pip 只补装剩余依赖，速度提升数倍。
ARCH="$(uname -m)"
case "$ARCH" in
    armv7l|armhf|armv6l|aarch64|arm64)
        log "检测到 ARM 架构（$ARCH），使用 apt 二进制包加速安装 pandas 等..."
        apt-get install -y -qq \
            python3-pandas python3-numpy python3-openpyxl python3-xlrd \
            python3-pil python3-yaml python3-requests >/dev/null 2>&1 || true
        VENV_EXTRA="--system-site-packages"
        ;;
    *)
        VENV_EXTRA=""
        ;;
esac
[ -d venv ] || python3 -m venv $VENV_EXTRA venv
# 国内网络下官方源（files.pythonhosted.org）常因 IPv6/DNS 卡死且不报错，
# 故默认走清华镜像并加超时上限：失败快速切换另一源，避免无限静默重试。
venv/bin/pip install --upgrade pip -q --timeout 30 --retries 1 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
if ! venv/bin/pip install -r requirements.txt -q --timeout 60 --retries 2 \
        -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null; then
    log "清华镜像安装失败，切换官方源重试..."
    venv/bin/pip install -r requirements.txt -q --timeout 60 --retries 2
fi
log "Python 依赖安装完成"

# ---- 6. 证书（CA + 服务器 + 客户端，mTLS）----
step "生成安全证书（10 年有效期，含本机 IP / 域名）"
bash scripts/gen_certs.sh "$CERT_DIR" "$DOMAINS"
[ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/client.key" ] \
    || { red "证书生成失败"; exit 1; }

# ---- 7. systemd 服务 ----
step "配置开机自启服务"
systemctl daemon-reload >/dev/null 2>&1 || true
SRV_SERVER="/etc/systemd/system/${SVC_PREFIX}-server.service"
SRV_STUNNEL="/etc/systemd/system/${SVC_PREFIX}-stunnel.service"
STUNNEL_CONF="/etc/stunnel/${SVC_PREFIX}.conf"

sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    -e "s|__INNER_PORT__|$INNER_PORT|g" \
    -e "s|__WORKERS__|$WORKERS|g" \
    deploy/population-server.service > "$SRV_SERVER"

mkdir -p /etc/stunnel
sed -e "s|__CERT_DIR__|$CERT_DIR|g" \
    -e "s|__PORT__|$PORT|g" \
    -e "s|__INNER_PORT__|$INNER_PORT|g" \
    -e "s|__NAME__|$SVC_PREFIX|g" \
    deploy/stunnel/population.conf > "$STUNNEL_CONF"

sed -e "s|__STUNNEL_BIN__|$STUNNEL_BIN|g" \
    -e "s|__CONF__|$STUNNEL_CONF|g" \
    -e "s|__NAME__|$SVC_PREFIX|g" \
    deploy/stunnel/population-stunnel.service > "$SRV_STUNNEL"

systemctl daemon-reload
systemctl enable "${SVC_PREFIX}-server" >/dev/null 2>&1
systemctl restart "${SVC_PREFIX}-server"
sleep 6
systemctl enable "${SVC_PREFIX}-stunnel" >/dev/null 2>&1
systemctl restart "${SVC_PREFIX}-stunnel"
sleep 2
log "服务已配置并启动"

# ---- 8. 验证 ----
step "验证安装结果"
ACTIVE=$(systemctl is-active "${SVC_PREFIX}-server" || true)
if [ "$ACTIVE" != "active" ]; then
    red "服务端未启动，查看日志: journalctl -u ${SVC_PREFIX}-server -n 50"
    exit 1
fi
ACTIVE_S=$(systemctl is-active "${SVC_PREFIX}-stunnel" || true)
[ "$ACTIVE_S" = "active" ] || yellow "stunnel 状态异常: $ACTIVE_S（请检查 journalctl -u ${SVC_PREFIX}-stunnel）"

H="$(curl -sk --cert "$CERT_DIR/client.crt" --key "$CERT_DIR/client.key" -m 10 \
     "https://127.0.0.1:$PORT/api/health" 2>/dev/null || true)"
case "$H" in
    *healthy*) green "健康检查通过（带客户端证书）: $H" ;;
    *) red "健康检查失败: $H"; exit 1 ;;
esac
if curl -sk -m 5 "https://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
    yellow "警告：无客户端证书也能访问，mTLS 未生效，请检查 $STUNNEL_CONF"
else
    green "mTLS 双向校验生效：无客户端证书的访问已被拒绝"
fi

# ---- 9. 汇总 ----
step "安装完成"
echo ""
echo "======================================================"
echo "  人口通服务端已安装成功！"
echo "======================================================"
echo ""
echo "服务器地址（手机/电脑登录时填写任意一个）："
for ip in $(hostname -I 2>/dev/null); do
    echo "    https://$ip:$PORT"
done
IPS6="$(ip -o -6 addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 || true)"
for ip6 in $IPS6; do
    echo "    https://[$ip6]:$PORT  （公网 IPv6）"
done
[ -n "$DOMAINS" ] && echo "    域名: https://$(echo "$DOMAINS" | cut -d, -f1):$PORT"
echo ""
echo "默认管理员账号: admin    密码: admin123"
echo "  （首次登录后请创建正式管理员，默认账号会自动禁用）"
echo ""
echo "客户端打包需要以下 3 个证书文件（已包含本机地址，务必使用本机生成的文件）："
echo "    $CERT_DIR/server.crt"
echo "    $CERT_DIR/client.crt"
echo "    $CERT_DIR/client.key"
echo "  一键导出: bash scripts/export_client_certs.sh"
echo ""
echo "常用管理命令："
echo "    查看状态: systemctl status ${SVC_PREFIX}-server ${SVC_PREFIX}-stunnel"
echo "    重启服务: systemctl restart ${SVC_PREFIX}-server ${SVC_PREFIX}-stunnel"
echo "    查看日志: journalctl -u ${SVC_PREFIX}-server -n 100"
echo "======================================================"
