"""户主守卫函数的统一调度出口（一函数一文件）。"""

from .relation_sets import (
    CHILD_RELS, SPOUSE_RELS, PARENT_RELS, INLAW_PARENT_RELS,
    GRAND_RELS, SIBLING_RELS, DEFAULT_DEMOTED,
)
from .norm_relation import norm_relation
from .infer_gender import infer_gender
from .birth_key import birth_key
from .classify_relation import classify_relation
from .parent_rel import parent_rel
from .reverse_spouse import reverse_spouse
from .grandparent_rel import grandparent_rel
from .outer_grandparent_rel import outer_grandparent_rel
from .sibling_rel import sibling_rel
from .set_relation import set_relation
from .find_head import find_head
from .demoted_relation import demoted_relation
from .rebuild_family_relations import rebuild_family_relations
from .demote_old_head import demote_old_head

__all__ = [
    'CHILD_RELS', 'SPOUSE_RELS', 'PARENT_RELS', 'INLAW_PARENT_RELS',
    'GRAND_RELS', 'SIBLING_RELS', 'DEFAULT_DEMOTED',
    'norm_relation', 'infer_gender', 'birth_key', 'classify_relation',
    'parent_rel', 'reverse_spouse', 'grandparent_rel', 'outer_grandparent_rel',
    'sibling_rel', 'set_relation',
    'find_head', 'demoted_relation', 'rebuild_family_relations', 'demote_old_head',
]
