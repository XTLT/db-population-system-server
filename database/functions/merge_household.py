"""merge_household 函数。"""

from ..models.person import Person
from .._base import get_session

def merge_household(target_hu_hao: str, person_ids: list):
    if not person_ids:
        raise ValueError("请选择要合户的人员")
    session = get_session()
    try:
        for pid in person_ids:
            p = session.query(Person).filter(Person.id == pid).first()
            if p:
                p.hu_hao = target_hu_hao
                from datetime import datetime
                p.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

