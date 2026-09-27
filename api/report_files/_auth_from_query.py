from flask import request

from utils.security import get_token_data


def _auth_from_query():
    """从 query string 获取 token（用于浏览器在线编辑页面）"""
    token = request.args.get('token', '')
    if not token:
        return None
    token_data = get_token_data(token)
    if not token_data:
        return None
    from datetime import datetime as _dt
    if _dt.now() > token_data['expires_at']:
        return None
    return token_data['user']
