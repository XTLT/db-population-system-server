"""add_operation_log 函数。"""

import secrets
from ..models.operation_log import OperationLog
from .._base import get_session

def add_operation_log(user_id: str, username: str, operation_type: str, operation_target: str = "", ip_address: str = "", client_type: str = "", is_high_risk: str = "否"):
    from datetime import datetime
    session = get_session()
    try:
        log = OperationLog(
            id=f"log_{secrets.token_hex(8)}",
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            operation_target=operation_target,
            ip_address=ip_address,
            client_type=client_type,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_high_risk=is_high_risk
        )
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

