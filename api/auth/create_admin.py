import secrets
from datetime import datetime
from flask import request, jsonify

from database import get_session, User, add_operation_log
from utils.security import hash_password
from utils.response import get_json_data, safe_exception
from utils import validate_username, validate_real_name
from database import validate_password
from . import bp


@bp.route('/create-admin', methods=['POST'])
def api_create_admin():
    """创建管理员账户
    
    两种模式：
    1. 已登录默认管理员：创建真实管理员
    2. 未登录且无真实管理员：创建第一个管理员（初始化）
    """
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

    session = get_session()
    try:
        # 检查是否已有真实管理员
        has_real_admin = session.query(User).filter(
            User.is_default != "是",
            User.role == "admin",
            User.is_active == "是"  # 只检查活跃的管理员
        ).first()
        
        # 如果已有真实管理员，需要认证
        if has_real_admin:
            # 检查是否已认证
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            from utils.security import get_token_data
            token_data = get_token_data(token)
            if not token or not token_data:
                return jsonify({'error': '系统已初始化，请登录管理员账户'}), 401
            
            token_data = get_token_data(token)
            if datetime.now() > token_data['expires_at']:
                return jsonify({'error': '登录已过期，请重新登录'}), 401
            
            current_user = token_data['user']
            
            # 检查当前用户是否为管理员
            if current_user.get('role') != 'admin':
                return jsonify({'error': '权限不足，仅管理员可执行此操作'}), 403
            
            # 检查当前用户是否活跃
            current_user_obj = session.query(User).filter(
                User.id == current_user['id']
            ).first()
            if not current_user_obj or current_user_obj.is_active != "是":
                return jsonify({'error': '账户已被禁用'}), 403

        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400

        existing = session.query(User).filter(User.username == username).first()
        if existing:
            return jsonify({'error': '用户名已存在'}), 400

        user = User(
            id=f"user_{secrets.token_hex(8)}",
            username=username,
            password_hash=hash_password(password),
            real_name=real_name,
            role="admin",
            is_default="否",
            is_active="是",  # 确保新用户是活跃的
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(user)

        # 禁用默认管理员账户
        default_user = session.query(User).filter(User.is_default == "是").first()
        if default_user:
            default_user.is_active = "否"

        session.commit()
        add_operation_log(user.id, user.username, "创建管理员账户", "", "", "Web")

        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        import traceback
        traceback.print_exc()
        return safe_exception(e, "创建用户失败", 400)
    finally:
        session.close()
