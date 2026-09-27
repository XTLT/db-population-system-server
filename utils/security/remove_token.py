from ._base import logger
from ._hash_token import _hash_token


def remove_token(token: str) -> bool:
    """从数据库删除 Token（通过哈希值删除）"""
    from database import get_session, Token

    token_hash = _hash_token(token)
    session = get_session()
    try:
        token_obj = session.query(Token).filter(Token.token == token_hash).first()
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
