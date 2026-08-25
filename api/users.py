import secrets
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify

from database import get_session, User, create_user, delete_user, get_all_users, add_operation_log
from utils.security import require_auth, hash_password, verify_password, DEFAULT_ADMIN_USERNAME
from utils.response import get_json_data, safe_exception
from utils import validate_username, validate_real_name, validate_phone
from database import validate_password


bp = Blueprint('users', __name__)


def _require_admin():
    """检查是否为管理员"""
    if request.current_user.get('role') != 'admin':
        return False
    return True


@bp.route('/')
@require_auth
def api_users():
    """获取用户列表（仅管理员）"""
    if not _require_admin():
        return jsonify({'error': '权限不足'}), 403
    users = get_all_users()
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'real_name': u.real_name,
            'role': u.role,
            'is_active': u.is_active,
            'is_default': u.is_default,
            'created_at': u.created_at or '',
            'last_login': u.last_login or '',
            'login_attempts': u.login_attempts or 0
        } for u in users]
    })


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


@bp.route('/<user_id>', methods=['DELETE'])
@require_auth
def api_delete_user(user_id):
    """删除用户（仅管理员）
    
    安全检查：
    - 不能删除自己
    - 不能删除最后一个管理员
    """
    if not _require_admin():
        return jsonify({'error': '权限不足'}), 403
    
    # 不能删除自己
    if request.current_user.get('id') == user_id:
        return jsonify({'error': '不能删除自己的账户'}), 400
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 不能删除最后一个管理员
        if user.role == 'admin':
            admin_count = session.query(User).filter(
                User.role == 'admin',
                User.is_active == '是'
            ).count()
            if admin_count <= 1:
                return jsonify({'error': '不能删除最后一个管理员'}), 400
        
        # 清除该用户的所有 Token（强制登出）
        from utils.security import remove_all_user_tokens
        remove_all_user_tokens(user_id)
        
        session.delete(user)
        session.commit()
        
        add_operation_log(
            request.current_user['id'], 
            request.current_user['username'], 
            "删除用户", 
            user.username, 
            request.remote_addr, 
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return safe_exception(e, "删除失败", 500)
    finally:
        session.close()


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


@bp.route('/<user_id>/reset-password', methods=['POST'])
@require_auth
def api_reset_password(user_id):
    """重置用户密码（仅管理员）
    
    安全措施：
    - 验证密码复杂度
    - 重置后强制用户重新登录
    """
    if not _require_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data, err = get_json_data()
    if err:
        return err
    
    new_password = data.get('password', '')
    
    # 验证密码复杂度
    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify({'error': msg}), 400
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user.password_hash = hash_password(new_password)
        user.login_attempts = "0"
        user.locked_until = ""
        
        # 如果是默认用户，清除默认标记
        if user.is_default == "是":
            user.is_default = "否"
        
        session.commit()
        
        # 清除该用户的所有 Token（强制重新登录）
        from utils.security import remove_all_user_tokens
        remove_all_user_tokens(user_id)
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "重置密码",
            user.username,
            request.remote_addr,
            "Web"
        )
        
        return jsonify({'success': True, 'message': '密码重置成功，用户需要重新登录'})
    except Exception as e:
        session.rollback()
        return safe_exception(e, "密码重置失败", 500)
    finally:
        session.close()
