"""证书工具的运行环境：目录常量与证书生成器入口（状态集中在这里）。"""

import os
import sys

SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加 server 目录到路径
sys.path.insert(0, os.path.join(SERVER_ROOT, 'server'))

try:
    from config import CERT_DIR
    from ssl_utils import generate_self_signed_cert
except ImportError:
    # 默认路径
    CERT_DIR = os.path.join(SERVER_ROOT, 'server', 'data', 'certs')

SCRIPT_DIR = SERVER_ROOT
