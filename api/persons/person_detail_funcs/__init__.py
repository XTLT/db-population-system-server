"""人员详情相关函数的统一调度出口。

外部只从这里取函数，新增/重写某个函数时只改对应文件，不影响调用方。
"""

from .to_amount import to_amount
from .build_person_detail import build_person_detail
from .build_base_row import build_base_row
from .add_health_item import add_health_item
from .api_person import api_person
from .api_person_subsidies import api_person_subsidies
from .api_pending_correction import api_pending_correction
from .api_mark_pending_correction import api_mark_pending_correction_handled
from .api_data_health import api_data_health
from .api_house_build import (
    api_house_build_batch_export,
    api_house_build_create,
    api_house_build_delete,
    api_house_build_detail,
    api_house_build_export,
    api_house_build_list,
    api_house_build_prefill,
    api_house_build_update,
)
from .subsidy_modules import SUBSIDY_MODULES, MAX_RECORDS, DATA_HEALTH_MAX_ITEMS

__all__ = [
    'to_amount',
    'build_person_detail',
    'build_base_row',
    'add_health_item',
    'api_person',
    'api_person_subsidies',
    'api_pending_correction',
    'api_mark_pending_correction_handled',
    'api_data_health',
    'api_house_build_list',
    'api_house_build_detail',
    'api_house_build_create',
    'api_house_build_update',
    'api_house_build_delete',
    'api_house_build_prefill',
    'api_house_build_export',
    'api_house_build_batch_export',
    'SUBSIDY_MODULES',
    'MAX_RECORDS',
    'DATA_HEALTH_MAX_ITEMS',
]
