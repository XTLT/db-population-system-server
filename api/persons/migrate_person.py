from flask import request, jsonify

from database import get_session, migrate_person, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/migrate', methods=['POST'])
@require_auth
def api_migrate_person(person_id):
    """迁移人员"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        real_id = p.id
    finally:
        session.close()
    migrate_person(
        real_id,
        data.get('date', ''),
        data.get('place', ''),
        data.get('reason', '')
    )
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "户籍迁出",
        person_id,
        request.remote_addr,
        "Web"
    )
    return jsonify({'success': True})
