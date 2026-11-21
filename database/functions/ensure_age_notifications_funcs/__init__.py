"""到龄提醒函数的统一调度出口。"""

from .next_month import next_month
from .parse_month import parse_month
from .alive_condition import alive_condition
from .not_migrated_condition import not_migrated_condition
from .query_age_group import query_age_group
from .query_age_group_unhandled import query_age_group_unhandled
from .format_age_content import format_age_content
from .ensure_age_notifications import ensure_age_notifications

__all__ = [
    'next_month', 'parse_month', 'alive_condition', 'not_migrated_condition',
    'query_age_group', 'query_age_group_unhandled', 'format_age_content',
    'ensure_age_notifications',
]
