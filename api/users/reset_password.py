from flask import request, jsonify

from database import get_session, User, add_operation_log
from utils.security import require_auth, hash_password
from utils.response import get_json_data, safe_exception
from database import validate_password
from . import bp
from ._helpers import _require_admin


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
