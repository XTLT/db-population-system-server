from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from . import bp


@bp.route('/persons/lookup-all')
@require_auth
def api_persons_lookup_all():
    """返回所有人员的全部业务字段，用于桌面端批量匹配填表"""
    session = get_session()
    try:
        persons = session.query(Person).all()
        all_fields = [c.key for c in Person.__table__.columns if c.key != 'id']
        result = []
        for p in persons:
            result.append({f: (getattr(p, f) or '') for f in all_fields})
        return jsonify({'persons': result, 'total': len(result)})
    finally:
        session.close()
