"""同为旧户主子女的两个成员互为兄弟姐妹：按出生日期 + 性别定 兄/弟/姐/妹。"""

from .norm_relation import norm_relation
from .birth_key import birth_key
from .infer_gender import infer_gender


def sibling_rel(new_head, member):
    nk, mk = birth_key(new_head.id_card), birth_key(member.id_card)
    mg = infer_gender(member.id_card)
    if nk and mk:
        if nk < mk:
            return ('弟' if mg != '女' else '妹')
        if nk > mk:
            return ('兄' if mg != '女' else '姐')
    # 无出生日期时按原关系保留排行：原为长子/长女类保持原名，其他归兄弟姐妹类
    rel = norm_relation(member.relation)
    if rel in ('长子', '长女', '之子', '之女', '子', '女'):
        return rel if mg != '女' else ('姐' if rel in ('长女', '之女', '女') else '妹')
    return '弟' if mg != '女' else '妹'
