"""add_report_log 函数。"""

from ..models.report_operation_log import ReportOperationLog
from .._base import get_session

def add_report_log(report_id: str, user_id: str, username: str,
                   operation_type: str, operation_detail: str = "",
                   ip_address: str = "", client_type: str = ""):
    from datetime import datetime
    import uuid
    session = get_session()
    try:
        log = ReportOperationLog(
            id=f"rlog_{uuid.uuid4().hex[:12]}",
            report_id=report_id,
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            operation_detail=operation_detail,
            ip_address=ip_address,
            client_type=client_type,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

