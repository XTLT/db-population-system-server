"""数据体检清单里每行人员的基础字段。"""


def build_base_row(p) -> dict:
    return {
        'person_id': p.id,
        'name': p.name or '',
        'id_card': (p.id_card or '').strip(),
        'hu_hao': (p.hu_hao or '').strip(),
        'group_name': p.group_name or '',
    }
