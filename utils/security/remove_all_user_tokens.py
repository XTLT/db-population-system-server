from ._base import logger


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
