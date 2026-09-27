from flask import request, jsonify

from utils.security import remove_token, require_auth
from . import bp


@bp.route('/logout', methods=['POST'])
@require_auth
def api_logout():
    """用户登出（需要认证）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    remove_token(token)
    return jsonify({'success': True})
