from flask import request, jsonify

from database import split_household, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/household/split', methods=['POST'])
@require_auth
def api_split_household():
    """分户"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    person_ids = data.get('person_ids', [])
    new_hu_hao = data.get('new_hu_hao', '')
    try:
        result_hu_hao = split_household(person_ids, new_hu_hao)
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "分户",
            f"新户号:{result_hu_hao}",
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True, 'new_hu_hao': result_hu_hao})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
