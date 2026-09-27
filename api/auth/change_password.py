from flask import request, jsonify

from database import get_session, User
from utils.security import require_auth, verify_password, hash_password
from utils.response import get_json_data, safe_exception
from database import validate_password
from . import bp


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
        is_valid, _ = verify_password(old_password, user.password_hash)
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
