from flask import request, jsonify

from database import add_new_household, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/household/add', methods=['POST'])
@require_auth
def api_add_household():
    """新增户"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    try:
        add_new_household(
            hu_hao=data.get('hu_hao', ''),
            name=data.get('name', ''),
            id_card=data.get('id_card', ''),
            relation=data.get('relation', '户主'),
            address=data.get('address', ''),
            group_name=data.get('group_name', ''),
            phone=data.get('phone', ''),
            land_area=data.get('land_area', ''),
            local_welfare_forest_area=data.get('local_welfare_forest_area', ''),
            national_welfare_forest_area=data.get('national_welfare_forest_area', ''),
            commercial_forest_area=data.get('commercial_forest_area', '')
        )
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "新增户",
            f"户号:{data.get('hu_hao')}",
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
