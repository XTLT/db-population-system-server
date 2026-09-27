from flask import request, jsonify

from database import get_session, User, add_operation_log
from utils.security import require_auth
from utils.response import safe_exception
from . import bp
from ._helpers import _require_admin


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
