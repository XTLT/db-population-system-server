import os
import secrets
import hashlib
import functools
import logging
import json
from datetime import datetime, timedelta
from flask import request, jsonify

logger = logging.getLogger('population_system')

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
    """创建 Token 并存储到数据库"""
    from database import get_session, Token
    
    token = secrets.token_hex(32)
    user_id = user_data.get('id')
    ip = request.remote_addr if request else 'unknown'
    expires_at = datetime.now() + timedelta(hours=expiry_hours)
    
    session = get_session()
    try:
        # 删除该用户的旧 token（超过最大并发数）
        existing_tokens = session.query(Token).filter(
            Token.user_id == user_id
        ).order_by(Token.created_at.desc()).all()
        
        if len(existing_tokens) >= MAX_CONCURRENT_SESSIONS:
            for old_token in existing_tokens[MAX_CONCURRENT_SESSIONS - 1:]:
                session.delete(old_token)
        
        # 创建新 token
        new_token = Token(
            token=token,
            user_id=user_id,
            user_data=json.dumps(user_data, ensure_ascii=False),
            expires_at=expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ip=ip
        )
        session.add(new_token)
        session.commit()
        
        logger.info(f"用户 {user_id} 创建新Token")
    except Exception as e:
        session.rollback()
        logger.error(f"创建Token失败: {e}")
        raise
    finally:
        session.close()
    
    return token


def get_token_data(token: str) -> dict:
    """从数据库获取 Token 数据"""
    from database import get_session, Token
    
    session = get_session()
    try:
        token_obj = session.query(Token).filter(Token.token == token).first()
        if not token_obj:
            return None
        
        return {
            'user': json.loads(token_obj.user_data),
            'expires_at': datetime.strptime(token_obj.expires_at, "%Y-%m-%d %H:%M:%S"),
            'created_at': datetime.strptime(token_obj.created_at, "%Y-%m-%d %H:%M:%S") if token_obj.created_at else datetime.now(),
            'ip': token_obj.ip
        }
    except Exception as e:
        logger.error(f"获取Token数据失败: {e}")
        return None
    finally:
        session.close()


def remove_token(token: str) -> bool:
    """从数据库删除 Token"""
    from database import get_session, Token
    
    session = get_session()
    try:
        token_obj = session.query(Token).filter(Token.token == token).first()
        if token_obj:
            session.delete(token_obj)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"删除Token失败: {e}")
        return False
    finally:
        session.close()


def remove_all_user_tokens(user_id: str) -> int:
    """删除用户的所有 Token"""
    from database import get_session, Token
    
    session = get_session()
    try:
        count = session.query(Token).filter(Token.user_id == user_id).delete()
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        logger.error(f"删除用户Token失败: {e}")
        return 0
    finally:
        session.close()


def cleanup_expired_tokens():
    """清理过期的 Token"""
    from database import get_session, Token
    
    session = get_session()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = session.query(Token).filter(Token.expires_at < now).delete()
        session.commit()
        if count > 0:
            logger.info(f"清理了 {count} 个过期Token")
        return count
    except Exception as e:
        session.rollback()
        logger.error(f"清理Token失败: {e}")
        return 0
    finally:
        session.close()


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
