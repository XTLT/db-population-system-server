"""get_report_logs 函数。"""

from ..models.report_operation_log import ReportOperationLog
from .._base import get_session

def get_report_logs(report_id: str) -> list:
    session = get_session()
    try:
        logs = session.query(ReportOperationLog).filter(
            ReportOperationLog.report_id == report_id
        ).order_by(ReportOperationLog.created_at.desc()).all()
        return [
            {
                'time': log.created_at,
                'user': log.username,
                'action': log.operation_type,
                'detail': log.operation_detail,
                'ip': log.ip_address,
            }
            for log in logs
        ]
    finally:
        session.close()

