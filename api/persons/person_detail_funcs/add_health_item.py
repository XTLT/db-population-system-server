"""往数据体检的某个分组追加一条人员记录。"""

from .build_base_row import build_base_row


def add_health_item(buckets, key, person, detail) -> None:
    row = build_base_row(person)
    row['detail'] = detail
    buckets[key]['items'].append(row)
