from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from . import bp


@bp.route('/persons/lookup-all')
@require_auth
def api_persons_lookup_all():
    """返回所有人员的关键字段，用于桌面端批量匹配填表"""
    session = get_session()
    try:
        persons = session.query(Person).all()
        result = []
        for p in persons:
            result.append({
                'name': p.name or '',
                'id_card': p.id_card or '',
                'phone': p.phone or '',
                'social_card1': p.social_card1 or '',
                'social_card2': p.social_card2 or '',
                'social_card3': p.social_card3 or '',
                'hu_hao': p.hu_hao or '',
                'address': p.address or '',
                'relation': p.relation or ''
            })
        return jsonify({'persons': result, 'total': len(result)})
    finally:
        session.close()
