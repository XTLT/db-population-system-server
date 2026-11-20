"""（保守单降级用）新户主原关系 + 旧户主性别 -> 旧户主应降级的关系。"""

from .norm_relation import norm_relation
from .infer_gender import infer_gender
from .parent_rel import parent_rel
from .reverse_spouse import reverse_spouse
from .grandparent_rel import grandparent_rel
from .relation_sets import (
    CHILD_RELS, SPOUSE_RELS, PARENT_RELS, DEFAULT_DEMOTED,
)


def demoted_relation(new_head_old_relation, old_head_id_card):
    rel = norm_relation(new_head_old_relation)
    gender = infer_gender(old_head_id_card)
    # 子女类
    if rel in CHILD_RELS:
        return parent_rel(gender)
    # 姻亲晚辈
    if rel == '儿媳':
        return '公公' if gender != '女' else '婆婆'
    if rel == '女婿':
        return '岳父' if gender != '女' else '岳母'
    if rel in ('孙子', '孙女', '之孙子', '之孙女'):
        return '祖父' if gender != '女' else '祖母'
    if rel in ('外孙子', '外孙女', '之外孙女'):
        return '外祖父' if gender != '女' else '外祖母'
    if rel in SPOUSE_RELS:
        return reverse_spouse(rel)
    if rel in PARENT_RELS:
        return grandparent_rel(gender)
    return DEFAULT_DEMOTED
