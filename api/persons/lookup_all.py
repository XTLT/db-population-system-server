from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from . import bp
from .offline_bundle_funcs import (
    build_educations_for_all,
    build_subsidies_for_all,
)


@bp.route('/persons/lookup-all')
@require_auth
def api_persons_lookup_all():
    """返回所有人员的全部业务字段。

    桌面端批量匹配填表默认只取人员；移动端离线全量包通过
    `with_subsidies=1&with_education=1` 额外拿到补贴与就读信息，
    旧客户端不传参数时响应结构保持不变。
    """
    session = get_session()
    try:
        persons = session.query(Person).all()
        all_fields = [c.key for c in Person.__table__.columns if c.key != 'id']
        result = []
        person_names = {}
        for p in persons:
            row = {f: (getattr(p, f) or '') for f in all_fields}
            result.append(row)
            id_card = (p.id_card or '').strip()
            if id_card:
                person_names[id_card] = p.name or ''

        payload = {'persons': result, 'total': len(result)}
        if request.args.get('with_subsidies') == '1':
            payload['subsidies'] = build_subsidies_for_all(session, person_names)
        if request.args.get('with_education') == '1':
            payload['educations'] = build_educations_for_all(session)
        return jsonify(payload)
    finally:
        session.close()
