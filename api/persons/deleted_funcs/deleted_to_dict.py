"""把 DeletedPerson ORM 对象序列化为前端期望的 dict。"""


def deleted_to_dict(d):
    return {
        'id': d.id,
        'original_id': d.original_id,
        'hu_hao': d.hu_hao,
        'id_card': d.id_card,
        'name': d.name,
        'age': d.age or '',
        'address': d.address or '',
        'group_name': getattr(d, 'group_name', '') or '',
        'relation': d.relation or '',
        'deleted_at': d.deleted_at or '',
    }
