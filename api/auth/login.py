import hashlib
from datetime import datetime, timedelta
from flask import request, jsonify

from database import get_session, User, add_operation_log
from utils.security import create_token, verify_password, hash_password
from utils.response import safe_exception
from config import TOKEN_EXPIRY_HOURS, LOGIN_LOCK_MINUTES
from . import bp


@bp.route('/login', methods=['POST'])
def api_login():
    """用户登录
    
    支持两种客户端模式：
    1. APP端：发送 sha256(原始密码)，password_hashed=True（仅支持旧SHA256格式）
    2. 网页端：发送原始密码，password_hashed=False（支持所有格式）
    """
    from utils.response import get_json_data
    data, err = get_json_data()
    if err:
        return err
    username = data.get('username', '')
    password = data.get('password', '')
    password_hashed = data.get('password_hashed', False)
    ip_address = request.remote_addr

    session = get_session()
    try:
        user_obj = session.query(User).filter(
            User.username == username, 
            User.is_active == "是"
        ).first()
        if not user_obj:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

        # 检查账户锁定
        if user_obj.locked_until:
            try:
                lock_time = datetime.strptime(user_obj.locked_until, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < lock_time:
                    remaining = int((lock_time - datetime.now()).total_seconds() / 60) + 1
                    return jsonify({
                        'success': False, 
                        'error': f'密码错误次数过多，账户已锁定，请{remaining}分钟后重试'
                    }), 429
                user_obj.locked_until = ""
                user_obj.login_attempts = "0"
            except Exception:
                user_obj.locked_until = ""
                user_obj.login_attempts = "0"

        stored_hash = user_obj.password_hash
        verified = False
        needs_rehash = False
        
        # 判断密码哈希格式
        if stored_hash.startswith("argon2:"):
            # Argon2 格式 - 只支持原始密码验证
            if password_hashed:
                # APP端发送预哈希密码，无法与Argon2验证
                return jsonify({
                    'success': False, 
                    'error': '请更新APP版本以支持新的安全认证方式'
                }), 400
            
            verified, needs_rehash = verify_password(password, stored_hash)
        else:
            # SHA256 格式（旧格式）
            try:
                parts = stored_hash.split(":")
                if stored_hash.startswith("sha256:"):
                    _, salt, hash_value = parts
                else:
                    salt, hash_value = parts
            except (ValueError, AttributeError):
                return jsonify({'success': False, 'error': '用户数据格式错误'}), 500
            
            if password_hashed:
                # APP端：客户端发送了 sha256(原始密码)
                computed = hashlib.sha256((salt + password).encode()).hexdigest()
                if computed == hash_value:
                    verified = True
                    needs_rehash = True  # 需要迁移到Argon2，但APP无法提供原始密码
            else:
                # 网页端：使用新的验证函数
                verified, needs_rehash = verify_password(password, stored_hash)
        
        if not verified:
            attempts = int(user_obj.login_attempts or "0") + 1
            user_obj.login_attempts = str(attempts)
            if attempts >= 5:
                user_obj.locked_until = (datetime.now() + timedelta(minutes=LOGIN_LOCK_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

        # 自动迁移到Argon2（仅网页端且非预哈希密码）
        if needs_rehash and not password_hashed:
            user_obj.password_hash = hash_password(password)
            session.commit()

        is_default = user_obj.is_default == "是"
        user_obj.login_attempts = "0"
        user_obj.locked_until = ""
        user_obj.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()

        # 统计登录前该用户在线会话数，用于提示"已有其他设备在线"
        from database import Token
        online_count = session.query(Token).filter(Token.user_id == user_obj.id).count()

        token = create_token({
            'id': user_obj.id,
            'username': user_obj.username,
            'real_name': user_obj.real_name,
            'role': user_obj.role,
            'is_default': user_obj.is_default
        }, TOKEN_EXPIRY_HOURS)
        
        add_operation_log(user_obj.id, user_obj.username, "登录", "", ip_address, "Web")

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': user_obj.username,
                'real_name': user_obj.real_name,
                'role': user_obj.role
            },
            'is_default_user': is_default,
            'require_password_change': is_default,
            'other_devices_online': online_count > 0,
            'warning': '已有其他设备在线' if online_count > 0 else ''
        })
    except Exception as e:
        session.rollback()
        import traceback
        traceback.print_exc()
        return safe_exception(e, "登录失败", 500)
    finally:
        session.close()
