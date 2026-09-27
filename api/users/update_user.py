from flask import request, jsonify

from database import get_session, User
from utils.security import require_auth, hash_password, verify_password
from utils.response import get_json_data
from . import bp


@bp.route('/<user_id>', methods=['PUT'])
@require_auth
def api_update_user(user_id):
    """更新用户信息"""
    is_admin = request.current_user.get('role') == 'admin'
    is_self = request.current_user.get('id') == user_id
    if not is_admin and not is_self:
        return jsonify({'error': '权限不足'}), 403
    
    data, err = get_json_data()
    if err:
        return err
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        if 'real_name' in data:
            user.real_name = data['real_name']
        if is_admin and 'role' in data:
            user.role = data['role']
        if is_admin and 'is_active' in data:
            # 不能禁用自己
            if user_id == request.current_user.get('id') and data['is_active'] == '否':
                return jsonify({'error': '不能禁用自己的账户'}), 400
            
            # 不能禁用最后一个管理员
            if user.role == 'admin' and data['is_active'] == '否':
                admin_count = session.query(User).filter(
                    User.role == 'admin',
                    User.is_active == '是'
                ).count()
                if admin_count <= 1:
                    return jsonify({'error': '不能禁用最后一个管理员'}), 400
            
            user.is_active = data['is_active']
            
            # 如果禁用用户，清除其所有 Token
            if data['is_active'] == '否':
                from utils.security import remove_all_user_tokens
                remove_all_user_tokens(user_id)
        if 'username' in data and data['username'] != user.username:
            existing = session.query(User).filter(User.username == data['username']).first()
            if existing:
                return jsonify({'error': '用户名已存在'}), 400
            user.username = data['username']
        if 'password' in data and data['password']:
            if not is_admin and 'old_password' in data:
                is_valid, _ = verify_password(data['old_password'], user.password_hash)
                if not is_valid:
                    return jsonify({'error': '原密码错误'}), 400
            user.password_hash = hash_password(data['password'])
        session.commit()
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
