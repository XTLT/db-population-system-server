import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from database import get_session, User, add_operation_log
from utils.security import (
    create_token, remove_token, require_auth,
    DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, hash_password, verify_password
)
from utils.response import safe_error, get_json_data, safe_exception
from utils import validate_username, validate_real_name
from config import TOKEN_EXPIRY_HOURS, LOGIN_LOCK_MINUTES
from database import validate_password, create_user, get_all_users


bp = Blueprint('auth', __name__)


def _ensure_default_admin():
    """创建默认管理员账户"""
    session = get_session()
    try:
        existing = session.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not existing:
            user = User(
                id=f"user_default_{secrets.token_hex(8)}",
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                real_name="初始管理员",
                role="admin",
                is_active="是",
                is_default="是",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(user)
            session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()


@bp.route('/status')
def api_status():
    """系统状态检查（公开端点，不暴露敏感信息）"""
    _ensure_default_admin()
    users = get_all_users()
    has_default = any(u.is_default == "是" for u in users)
    has_real_admin = any(u.is_default != "是" and u.role == "admin" for u in users)
    return jsonify({
        'initialized': len(users) > 0,
        'has_default_admin': has_default,
        'need_create_admin': has_default and not has_real_admin
    })


@bp.route('/health')
def api_health():
    """健康检查端点（移动端域名检查使用）"""
    return jsonify({'status': 'ok', 'healthy': True})


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


@bp.route('/login', methods=['POST'])
def api_login():
    """用户登录
    
    支持两种客户端模式：
    1. APP端：发送 sha256(原始密码)，password_hashed=True（仅支持旧SHA256格式）
    2. 网页端：发送原始密码，password_hashed=False（支持所有格式）
    """
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
            'require_password_change': is_default
        })
    except Exception as e:
        session.rollback()
        import traceback
        traceback.print_exc()
        return safe_exception(e, "登录失败", 500)
    finally:
        session.close()


@bp.route('/logout', methods=['POST'])
@require_auth
def api_logout():
    """用户登出（需要认证）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    remove_token(token)
    return jsonify({'success': True})


@bp.route('/check_token')
@require_auth
def api_check_token():
    """检查 Token 是否有效"""
    return jsonify({
        'valid': True,
        'user': request.current_user
    })


@bp.route('/change_password', methods=['POST'])
@require_auth
def api_change_password():
    """修改密码
    
    安全措施：
    - 验证旧密码
    - 验证新密码复杂度
    - 修改后清除所有 Token（强制重新登录）
    """
    data, err = get_json_data()
    if err:
        return err
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify({'error': msg}), 400
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == request.current_user['id']).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 验证旧密码
        is_valid, needs_rehash = verify_password(old_password, user.password_hash)
        if not is_valid:
            return jsonify({'error': '原密码错误'}), 400
        
        # 更新密码
        user.password_hash = hash_password(new_password)
        user.is_default = "否"  # 清除默认用户标记
        session.commit()
        
        # 清除该用户的所有 Token（强制重新登录）
        from utils.security import remove_all_user_tokens
        remove_all_user_tokens(user.id)
        
        return jsonify({
            'success': True, 
            'message': '密码修改成功，请重新登录',
            'require_relogin': True
        })
    except Exception as e:
        session.rollback()
        return safe_exception(e, "密码修改失败", 500)
    finally:
        session.close()


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
