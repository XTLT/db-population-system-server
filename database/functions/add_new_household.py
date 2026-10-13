"""add_new_household 函数。"""

import secrets
from ..models.person import Person
from .._base import get_session

def add_new_household(hu_hao: str, name: str, id_card: str, relation: str = "户主", **kwargs) -> Person:
    session = get_session()
    try:
        # 验证身份证号格式
        from utils import validate_id_card, validate_phone
        valid, msg = validate_id_card(id_card)
        if not valid:
            raise ValueError(msg)
        
        # 验证电话号码（如果提供）
        phone = kwargs.get("phone", "")
        if phone:
            valid, msg = validate_phone(phone)
            if not valid:
                raise ValueError(f"电话号码: {msg}")
        
        existing = session.query(Person).filter(Person.hu_hao == hu_hao).first()
        if existing:
            raise ValueError(f"户号 {hu_hao} 已存在")
        from utils import calculate_age
        person = Person(
            id=f"p_{hu_hao}_{secrets.token_hex(4)}",  # 使用随机ID，避免可预测性
            hu_hao=hu_hao,
            id_card=id_card,
            name=name,
            age=calculate_age(id_card),
            relation=relation,
            address=kwargs.get("address", ""),
            group_name=kwargs.get("group_name", ""),
            phone=phone,
            land_area=kwargs.get("land_area", ""),
            local_welfare_forest_area=kwargs.get("local_welfare_forest_area", ""),
            national_welfare_forest_area=kwargs.get("national_welfare_forest_area", ""),
            commercial_forest_area=kwargs.get("commercial_forest_area", ""),
        )
        session.add(person)
        session.commit()
        return person
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

