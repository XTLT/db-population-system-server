"""保守单降级：把该户现有户主降级为匹配关系（兼容旧调用）。"""

from datetime import datetime

from ..._base import get_session
from .find_head import find_head
from .demoted_relation import demoted_relation


def demote_old_head(hu_hao, exclude_id, new_head_old_relation):
    session = get_session()
    try:
        old_head = find_head(session, hu_hao, exclude_id=exclude_id)
        if old_head is None:
            return None
        old_head.relation = demoted_relation(new_head_old_relation, old_head.id_card)
        old_head.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.merge(old_head)
        session.commit()
        return old_head
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
