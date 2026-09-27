from datetime import datetime
from ._base import logger


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
