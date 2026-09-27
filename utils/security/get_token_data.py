import json
from datetime import datetime
from ._base import logger
from ._hash_token import _hash_token


def get_token_data(token: str) -> dict:
    """从数据库获取 Token 数据（通过哈希值查询）"""
    from database import get_session, Token

    token_hash = _hash_token(token)  # 计算哈希值用于查询
    session = get_session()
    try:
        token_obj = session.query(Token).filter(Token.token == token_hash).first()
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
