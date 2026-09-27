from flask import jsonify

from database import Person
from utils.security import check_id_card_rate_limit


def safe_id_card_query(session, person_id: str):
    p = session.query(Person).filter(Person.id == person_id).first()
    if p:
        return p, None
    
    if len(person_id) == 18 and (person_id[:-1].isdigit() and person_id[-1] in '0123456789xX'):
        is_allowed, remaining = check_id_card_rate_limit(person_id)
        if not is_allowed:
            return None, (jsonify({
                'error': f'查询过于频繁，请等待{remaining}秒后重试'
            }), 429)
        
        p = session.query(Person).filter(Person.id_card == person_id).first()
        if p:
            return p, None
    
    return None, (jsonify({'error': 'Not found'}), 404)
