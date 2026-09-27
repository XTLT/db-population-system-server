"""change_user_password 函数。"""

from ..models.user import User
from .._base import get_session
from utils.security import hash_password, verify_password
from .validate_password import validate_password

def change_user_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    valid, msg = validate_password(new_password)
    if not valid:
        return False, msg
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        
        is_valid, _ = verify_password(old_password, user.password_hash)
        if not is_valid:
            return False, "原密码错误"
        
        user.password_hash = hash_password(new_password)
        session.commit()
        return True, ""
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

