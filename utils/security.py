import os
import secrets
import hashlib
import functools
import logging
import threading
from datetime import datetime, timedelta
from flask import request, jsonify

logger = logging.getLogger('population_system')

_tokens = {}
_user_tokens = {}
_token_lock = threading.Lock()
MAX_CONCURRENT_SESSIONS = 3
DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_sha256 = hashlib.sha256(password.encode()).hexdigest()
    password_hash = hashlib.sha256((salt + password_sha256).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, stored_hash = password_hash.split(":")
        
        password_sha256 = hashlib.sha256(password.encode()).hexdigest()
        new_format_hash = hashlib.sha256((salt + password_sha256).encode()).hexdigest()
        if new_format_hash == stored_hash:
            return True
        
        old_format_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        if old_format_hash == stored_hash:
            return True
        
        return False
    except Exception:
        return False


def create_token(user_data: dict, expiry_hours: int = 24) -> str:
    token = secrets.token_hex(32)
    user_id = user_data.get('id')
    ip = request.remote_addr if request else 'unknown'
    
    with _token_lock:
        _tokens[token] = {
            'user': user_data,
            'expires_at': datetime.now() + timedelta(hours=expiry_hours),
            'created_at': datetime.now(),
            'ip': ip
        }
        
        if user_id not in _user_tokens:
            _user_tokens[user_id] = []
        
        _user_tokens[user_id].append(token)
        
        if len(_user_tokens[user_id]) > MAX_CONCURRENT_SESSIONS:
            oldest_token = _user_tokens[user_id].pop(0)
            if oldest_token in _tokens:
                del _tokens[oldest_token]
                logger.info(f"用户 {user_id} 超过最大并发登录数，移除旧Token")
    
    return token


def get_token_data(token: str) -> dict:
    with _token_lock:
        return _tokens.get(token)


def remove_token(token: str) -> bool:
    with _token_lock:
        if token in _tokens:
            user_id = _tokens[token]['user'].get('id')
            del _tokens[token]
            
            if user_id and user_id in _user_tokens:
                if token in _user_tokens[user_id]:
                    _user_tokens[user_id].remove(token)
                if not _user_tokens[user_id]:
                    del _user_tokens[user_id]
            
            return True
        return False


def remove_all_user_tokens(user_id: str) -> int:
    count = 0
    with _token_lock:
        if user_id in _user_tokens:
            for token in _user_tokens[user_id]:
                if token in _tokens:
                    del _tokens[token]
                    count += 1
            del _user_tokens[user_id]
    return count


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        with _token_lock:
            if not token or token not in _tokens:
                return jsonify({'error': '未授权访问'}), 401
            token_data = _tokens[token]
            if datetime.now() > token_data['expires_at']:
                del _tokens[token]
                return jsonify({'error': '登录已过期，请重新登录'}), 401
            
            current_ip = request.remote_addr
            if token_data.get('ip') and token_data['ip'] != current_ip:
                logger.warning(f"Token IP变化: {token_data['ip']} -> {current_ip}, 用户: {token_data['user'].get('username')}")
            
            request.current_user = token_data['user']
        
        return f(*args, **kwargs)
    return decorated


_id_card_query_times = {}
ID_CARD_QUERY_LIMIT = 30
ID_CARD_QUERY_WINDOW = 60


def check_id_card_rate_limit(person_id: str) -> tuple:
    ip = request.remote_addr
    now = datetime.now()
    
    if ip in _id_card_query_times:
        _id_card_query_times[ip] = [
            (ts, pid) for ts, pid in _id_card_query_times[ip]
            if (now - ts).total_seconds() < ID_CARD_QUERY_WINDOW
        ]
    
    if ip not in _id_card_query_times:
        _id_card_query_times[ip] = []
    
    query_count = len(_id_card_query_times[ip])
    
    if query_count >= ID_CARD_QUERY_LIMIT:
        oldest = _id_card_query_times[ip][0][0]
        remaining = ID_CARD_QUERY_WINDOW - (now - oldest).total_seconds()
        return False, int(remaining)
    
    _id_card_query_times[ip].append((now, person_id))
    return True, 0
