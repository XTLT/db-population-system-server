"""已删除人员路由注册入口（函数实现见 deleted_funcs/）。"""

from . import bp
from .deleted_funcs import (
    api_list_deleted,
    api_recover_person,
    api_purge_deleted,
)

bp.add_url_rule('/deleted', endpoint='api_list_deleted', view_func=api_list_deleted,
                methods=['GET'])
bp.add_url_rule('/recover/<deleted_id>', endpoint='api_recover_person',
                view_func=api_recover_person, methods=['POST'])
bp.add_url_rule('/deleted/purge', endpoint='api_purge_deleted',
                view_func=api_purge_deleted, methods=['POST'])
