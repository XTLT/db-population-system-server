"""split_household 函数。"""

from ..models.person import Person
from .._base import get_session
from .generate_new_hu_hao import generate_new_hu_hao

def split_household(person_ids: list, new_hu_hao: str = None) -> str:
    if not person_ids:
        raise ValueError("请选择要分户的人员")
    if not new_hu_hao:
        new_hu_hao = generate_new_hu_hao()
    session = get_session()
    try:
        for pid in person_ids:
            p = session.query(Person).filter(Person.id == pid).first()
            if p:
                p.hu_hao = new_hu_hao
                p.relation = "户主"
                from datetime import datetime
                p.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        return new_hu_hao
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

