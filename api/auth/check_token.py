from flask import request, jsonify

from utils.security import require_auth
from . import bp


@bp.route('/check_token')
@require_auth
def api_check_token():
    """检查 Token 是否有效"""
    return jsonify({
        'valid': True,
        'user': request.current_user
    })
