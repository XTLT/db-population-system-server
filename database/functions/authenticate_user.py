"""authenticate_user 函数。"""

import hashlib
from ..models.user import User
from .._base import get_session

def authenticate_user(username: str, password: str, ip_address: str = "", client_type: str = "") -> User | None:
    from datetime import datetime, timedelta
    session = get_session()
    try:
        user = session.query(User).filter(User.username == username, User.is_active == "是").first()
        if not user:
            return None
        if user.locked_until:
            try:
                lock_time = datetime.strptime(user.locked_until, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < lock_time:
                    return None
                user.locked_until = ""
                user.login_attempts = "0"
            except Exception:
                user.locked_until = ""
                user.login_attempts = "0"
        salt, stored_hash = user.password_hash.split(":")
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        if password_hash != stored_hash:
            attempts = int(user.login_attempts or "0") + 1
            user.login_attempts = str(attempts)
            if attempts >= 5:
                user.locked_until = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            return None
        user.login_attempts = "0"
        user.locked_until = ""
        user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        result = type('UserResult', (), {
            'id': user.id, 'username': user.username, 'real_name': user.real_name,
            'role': user.role, 'is_active': user.is_active
        })()
        return result
    finally:
        session.close()

