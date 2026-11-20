"""POST /api/persons/recover/<deleted_id>：找回已删除人员（管理员）。"""

from flask import request, jsonify
from utils.security import get_client_ip, require_auth

from database import (
    get_session, recover_person, DeletedPerson, add_operation_log,
)


@require_auth
def api_recover_person(deleted_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'success': False, 'error': '权限不足'}), 403

    # 先确认该删除记录存在，否则 recover_person 会静默不做事
    session = get_session()
    try:
        deleted = session.query(DeletedPerson).filter(DeletedPerson.id == deleted_id).first()
        if deleted is None:
            return jsonify({'success': False, 'error': '该删除记录不存在或已被找回'}), 404
        name = deleted.name
        id_card = deleted.id_card
    finally:
        session.close()

    try:
        recover_person(deleted_id)
    except Exception as e:
        return jsonify({'success': False, 'error': f'找回失败: {e}'}), 500

    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "找回人员",
        f"{name}({id_card[:6]}****{id_card[-4:]})" if id_card else name,
        get_client_ip(),
        "Web",
        "是"
    )
    return jsonify({'success': True})
