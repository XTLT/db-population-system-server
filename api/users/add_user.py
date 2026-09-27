from flask import request, jsonify

from database import create_user, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from utils import validate_username, validate_real_name
from . import bp
from ._helpers import _require_admin


@bp.route('/', methods=['POST'])
@require_auth
def api_add_user():
    """添加用户（仅管理员）"""
    if not _require_admin():
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    
    # 验证必填字段
    username = data.get('username', '')
    password = data.get('password', '')
    real_name = data.get('real_name', '')
    role = data.get('role', 'user')
    
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if not password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 验证用户名格式
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'error': msg}), 400
    
    # 验证真实姓名格式（如果提供）
    if real_name:
        valid, msg = validate_real_name(real_name)
        if not valid:
            return jsonify({'error': msg}), 400
    
    # 验证角色
    if role not in ['admin', 'user']:
        return jsonify({'error': '无效的用户角色'}), 400
    
    try:
        create_user(username, password, real_name, role)
        add_operation_log(
            request.current_user['id'], 
            request.current_user['username'], 
            "添加用户", 
            username, 
            request.remote_addr, 
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
