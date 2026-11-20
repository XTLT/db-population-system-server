"""检查更新相关函数的统一调度出口。"""

from .constants import SERVER_DIRECT_MIN_CODE
from .gitee_fallback import gitee_fallback
from .check_update_view import check_update

__all__ = ['SERVER_DIRECT_MIN_CODE', 'gitee_fallback', 'check_update']
