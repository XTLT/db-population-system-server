from flask import request, jsonify

from database import get_session, get_deleted_persons, recover_person, DeletedPerson, add_operation_log
from utils.security import require_auth
from . import bp


def _deleted_to_dict(d):
    """把 DeletedPerson ORM 对象序列化为前端期望的 dict。"""
    return {
        'id': d.id,
        'original_id': d.original_id,
        'hu_hao': d.hu_hao,
        'id_card': d.id_card,
        'name': d.name,
        'age': d.age or '',
        'address': d.address or '',
        'relation': d.relation or '',
        'deleted_at': d.deleted_at or '',
    }


@bp.route('/deleted', methods=['GET'])
@require_auth
def api_list_deleted():
    """列出已删除人员（供“找回人员”弹窗使用）。"""
    deleted = get_deleted_persons()
    return jsonify([_deleted_to_dict(d) for d in deleted])


@bp.route('/recover/<deleted_id>', methods=['POST'])
@require_auth
def api_recover_person(deleted_id):
    """找回（恢复）已删除人员。"""
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
        request.remote_addr,
        "Web",
        "是"
    )
    return jsonify({'success': True})
