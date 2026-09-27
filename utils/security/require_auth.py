import functools
from datetime import datetime
from flask import request, jsonify
from ._base import logger
from .get_token_data import get_token_data
from .remove_token import remove_token


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'error': '未授权访问'}), 401

        token_data = get_token_data(token)
        if not token_data:
            return jsonify({'error': '未授权访问'}), 401

        if datetime.now() > token_data['expires_at']:
            remove_token(token)
            return jsonify({'error': '登录已过期，请重新登录'}), 401

        current_ip = request.remote_addr
        if token_data.get('ip') and token_data['ip'] != current_ip:
            logger.warning(f"Token IP变化: {token_data['ip']} -> {current_ip}, 用户: {token_data['user'].get('username')}")

        request.current_user = token_data['user']

        return f(*args, **kwargs)
    return decorated
