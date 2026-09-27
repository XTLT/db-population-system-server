from flask import request, jsonify

from database import merge_household, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/household/merge', methods=['POST'])
@require_auth
def api_merge_household():
    """并户"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    target_hu_hao = data.get('target_hu_hao', '')
    person_ids = data.get('person_ids', [])
    try:
        merge_household(target_hu_hao, person_ids)
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "合户",
            f"目标户号:{target_hu_hao}",
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
