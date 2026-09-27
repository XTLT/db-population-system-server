from flask import request, jsonify

from database import get_session, delete_person, add_operation_log
from utils.security import require_auth
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>', methods=['DELETE'])
@require_auth
def api_delete_person(person_id):
    """删除人员"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        real_id = p.id
    finally:
        session.close()
    delete_person(real_id)
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "删除人员",
        person_id,
        request.remote_addr,
        "Web",
        "是"
    )
    return jsonify({'success': True})
