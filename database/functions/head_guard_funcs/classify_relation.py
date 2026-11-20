"""把关系分类：child/spouse/parent/inlaw_parent/grand/sibling/other。"""

from .norm_relation import norm_relation
from .relation_sets import (
    CHILD_RELS, SPOUSE_RELS, PARENT_RELS,
    INLAW_PARENT_RELS, GRAND_RELS, SIBLING_RELS,
)


def classify_relation(rel):
    rel = norm_relation(rel)
    if rel in CHILD_RELS:
        return 'child'
    if rel in SPOUSE_RELS:
        return 'spouse'
    if rel in PARENT_RELS:
        return 'parent'
    if rel in INLAW_PARENT_RELS:
        return 'inlaw_parent'
    if rel in GRAND_RELS:
        return 'grand'
    if rel in SIBLING_RELS:
        return 'sibling'
    return 'other'
