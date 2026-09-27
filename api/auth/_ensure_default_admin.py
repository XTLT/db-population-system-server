import secrets
from datetime import datetime

from database import get_session, User
from utils.security import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, hash_password


def _ensure_default_admin():
    """创建默认管理员账户"""
    session = get_session()
    try:
        existing = session.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not existing:
            user = User(
                id=f"user_default_{secrets.token_hex(8)}",
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                real_name="初始管理员",
                role="admin",
                is_active="是",
                is_default="是",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(user)
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
