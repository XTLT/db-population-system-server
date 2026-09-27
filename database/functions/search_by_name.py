"""search_by_name 函数。"""

from ..models.person import Person
from .._base import get_session

def search_by_name(name: str) -> list[Person]:
    import re
    from sqlalchemy import case
    session = get_session()
    try:
        # 转义LIKE特殊字符: % 匹配任意字符, _ 匹配单个字符
        escaped_name = re.sub(r'([%_])', r'\\\1', name)

        # 按相关性排序：精确匹配 > 前缀匹配 > 包含匹配
        relevance = case(
            (Person.name == name, 0),
            (Person.name.like(f"{escaped_name}%", escape='\\'), 1),
            else_=2
        )

        return session.query(Person).filter(
            Person.name.like(f"%{escaped_name}%", escape='\\')
        ).order_by(relevance, Person.name).limit(100).all()
    finally:
        session.close()

