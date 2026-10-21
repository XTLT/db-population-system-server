import os
from flask import Blueprint

from config import LOG_DIR

bp = Blueprint('update', __name__)

# Gitee仓库配置（拆分后三端各自发布到对应仓库；更新渠道已从GitHub切换为Gitee）
GITEE_OWNER = 'tension0712'
# /api/update/check?type=xxx 按端取对应仓库的 releases：
#   mobile  -> 移动端 APK（db-population-system-mobile）
#   desktop -> 桌面端安装包（db-population-system-desktop）
#   server  -> 服务端（自更新走 git pull，release 仅作镜像）
RELEASE_REPOS = {
    'mobile': 'db-population-system-mobile',
    'desktop': 'db-population-system-desktop',
    'server': 'db-population-system-server',
}
# 未知/缺省 type 时的兜底仓库（移动端是最常用的检查方）
DEFAULT_RELEASE_TYPE = 'mobile'


def release_api_url(repo):
    """拼接指定仓库的 Gitee releases API 地址（公开仓库匿名可读）"""
    return f'https://gitee.com/api/v5/repos/{GITEE_OWNER}/{repo}/releases'


# 缓存（按仓库分别缓存，避免三端 release 互相覆盖）
_cache = {}
CACHE_TTL = 300

_DEPLOY_LOG = os.path.join(LOG_DIR, 'server_update.log')
os.makedirs(LOG_DIR, exist_ok=True)

from . import _fetch_releases  # noqa: E402,F401
from . import _find_asset  # noqa: E402,F401
from . import _parse_version  # noqa: E402,F401
from . import _check_local_package  # noqa: E402,F401
from . import check_update  # noqa: E402,F401
from . import download_update  # noqa: E402,F401
from . import update_server  # noqa: E402,F401
from . import server_update_status  # noqa: E402,F401
