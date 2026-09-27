"""create_user 函数。"""

import hashlib
import secrets
from ..models.user import User
from .._base import get_session
from .validate_password import validate_password

def create_user(username: str, password: str, real_name: str = "", role: str = "user") -> User:
    from datetime import datetime
    valid, msg = validate_password(password)
    if not valid:
        raise ValueError(msg)
    session = get_session()
    try:
        existing = session.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("用户名已存在")
        salt = secrets.token_hex(16)
        # 使用双重哈希：sha256(salt + sha256(原始密码))
        password_sha256 = hashlib.sha256(password.encode()).hexdigest()
        password_hash = hashlib.sha256((salt + password_sha256).encode()).hexdigest()
        user = User(
            id=f"user_{secrets.token_hex(8)}",
            username=username,
            password_hash=f"{salt}:{password_hash}",
            real_name=real_name,
            role=role,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(user)
        session.commit()
        return user
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

