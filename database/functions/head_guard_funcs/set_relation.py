"""往变更列表里记一条关系变更（同值不记）。"""

from .norm_relation import norm_relation


def set_relation(session, changes, now, member, new_rel):
    cur = norm_relation(member.relation)
    if cur != new_rel:
        changes.append((member.name, cur, new_rel))
        member.relation = new_rel
        member.updated_at = now
        session.merge(member)
