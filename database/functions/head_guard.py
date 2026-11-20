"""每户唯一户主守卫 + 换户主整户关系重建。

函数实现已按一函数一文件拆到 head_guard_funcs/，本文件只做统一导出，
外部 `from database.functions.head_guard import ...` 的调用方式不变。
"""

from .head_guard_funcs import (
    find_head,
    demoted_relation,
    rebuild_family_relations,
    demote_old_head,
)

__all__ = [
    'find_head',
    'demoted_relation',
    'rebuild_family_relations',
    'demote_old_head',
]
