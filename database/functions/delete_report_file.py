"""delete_report_file 函数。"""

from ..models.report_file import ReportFile
from .._base import get_session

def delete_report_file(report_id: str) -> bool:
    session = get_session()
    try:
        r = session.query(ReportFile).filter(ReportFile.id == report_id).first()
        if r:
            session.delete(r)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

