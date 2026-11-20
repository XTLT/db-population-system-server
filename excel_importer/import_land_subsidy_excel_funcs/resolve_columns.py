"""根据别名表在实际列名中定位每个逻辑字段对应的列名。"""

from .land_subsidy_column_aliases import LAND_SUBSIDY_COLUMN_ALIASES


def resolve_columns(columns, aliases=LAND_SUBSIDY_COLUMN_ALIASES):
    resolved = {}
    used = set()
    for field, names in aliases.items():
        for n in names:
            if n in columns and n not in used:
                resolved[field] = n
                used.add(n)
                break
        else:
            resolved[field] = None
    return resolved
