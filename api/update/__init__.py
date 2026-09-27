import os
from flask import Blueprint

from config import LOG_DIR

bp = Blueprint('update', __name__)

# GitHub仓库配置
GITHUB_OWNER = 'XTLT'
GITHUB_REPO = 'db-population-system'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases'

# 缓存
_cache = {'data': None, 'timestamp': 0}
CACHE_TTL = 300

_DEPLOY_LOG = os.path.join(LOG_DIR, 'server_update.log')
os.makedirs(LOG_DIR, exist_ok=True)

from . import _fetch_releases  # noqa: E402,F401
from . import _find_asset  # noqa: E402,F401
from . import _parse_version  # noqa: E402,F401
from . import check_update  # noqa: E402,F401
from . import update_server  # noqa: E402,F401
from . import server_update_status  # noqa: E402,F401
