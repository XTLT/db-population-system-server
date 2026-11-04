from flask import request

from utils.security import get_token_data


def _auth_from_query():
    """获取当前用户（在线编辑接口共用）

    兼容两种携带方式：
    1. 浏览器：query string ?token=xxx（原有方式）
    2. desktop 客户端：Authorization: Bearer xxx（与 require_auth 一致）
    """
    token = request.args.get('token', '')
    if not token:
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
    if not token:
        return None
    token_data = get_token_data(token)
    if not token_data:
        return None
    from datetime import datetime as _dt
    if _dt.now() > token_data['expires_at']:
        return None
    return token_data['user']
