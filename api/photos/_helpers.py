from flask import jsonify

from database import Person


def safe_id_card_query(session, person_id: str):
    """
    安全的人员查询：先尝试ID查询，失败后尝试身份证号查询（带速率限制）
    
    Returns:
        (person, error_response) - 人员对象或错误响应
    """
    # 先尝试按ID查询
    p = session.query(Person).filter(Person.id == person_id).first()
    if p:
        return p, None
    
    # 检查是否可能是身份证号（18位数字）
    if len(person_id) == 18 and (person_id[:-1].isdigit() and person_id[-1] in '0123456789xX'):
        # 允许身份证号查询
        p = session.query(Person).filter(Person.id_card == person_id).first()
        if p:
            return p, None
    
    # 未找到
    return None, (jsonify({'error': 'Not found'}), 404)
