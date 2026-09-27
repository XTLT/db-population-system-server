"""delete_custom_report 函数。"""

from ..models.custom_report import CustomReport
from .._base import get_session

def delete_custom_report(report_id: str) -> bool:
    session = get_session()
    try:
        report = session.query(CustomReport).filter(CustomReport.id == report_id).first()
        if report:
            session.delete(report)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

