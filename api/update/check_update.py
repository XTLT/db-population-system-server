"""GET /api/update/check 的路由注册入口（函数实现见 check_update_funcs/）。"""

from . import bp
from .check_update_funcs import check_update

bp.add_url_rule('/check', endpoint='check_update', view_func=check_update)
