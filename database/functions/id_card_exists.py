"""id_card_exists 函数。"""

from ..models.person import Person
from .._base import get_session

def id_card_exists(id_card: str) -> bool:
    """检查身份证号在全局是否已存在（不限户号）"""
    session = get_session()
    try:
        return session.query(Person).filter(Person.id_card == id_card).first() is not None
    finally:
        session.close()

