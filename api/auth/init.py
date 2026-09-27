from flask import request, jsonify

from utils.response import get_json_data
from utils import validate_username, validate_real_name
from database import get_all_users, validate_password, create_user
from . import bp


@bp.route('/init', methods=['POST'])
def api_init():
    """系统初始化"""
    data, err = get_json_data()
    if err:
        return err
    username = data.get('username', '')
    password = data.get('password', '')
    real_name = data.get('real_name', '')
    
    # 验证用户名格式
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'error': msg}), 400
    
    # 验证真实姓名格式（如果提供）
    if real_name:
        valid, msg = validate_real_name(real_name)
        if not valid:
            return jsonify({'error': msg}), 400
    
    users = get_all_users()
    if users:
        return jsonify({'error': '系统已初始化'}), 400
    valid, msg = validate_password(password)
    if not valid:
        return jsonify({'error': msg}), 400
    try:
        create_user(username, password, real_name, "admin")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
