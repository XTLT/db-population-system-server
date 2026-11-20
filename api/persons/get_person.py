"""人员详情相关路由的注册入口。

函数实现全部在 person_detail_funcs/ 下（一函数一文件），
本文件只负责把视图函数挂到 persons 蓝图上，保持 URL 与 endpoint 不变。
"""

from . import bp
from .person_detail_funcs import (
    api_person,
    api_person_subsidies,
    api_pending_correction,
    api_data_health,
)

bp.add_url_rule('/person/<person_id>', endpoint='api_person', view_func=api_person)
bp.add_url_rule(
    '/person/<person_id>/subsidies',
    endpoint='api_person_subsidies',
    view_func=api_person_subsidies,
)
bp.add_url_rule(
    '/persons/pending-correction',
    endpoint='api_pending_correction',
    view_func=api_pending_correction,
)
bp.add_url_rule(
    '/persons/data-health',
    endpoint='api_data_health',
    view_func=api_data_health,
)
