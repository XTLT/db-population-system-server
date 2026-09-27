"""get_report_files 函数。"""

from ..models.report_file import ReportFile
from .._base import get_session

def get_report_files() -> list:
    session = get_session()
    try:
        reports = session.query(ReportFile).order_by(
            ReportFile.created_at.desc()
        ).all()
        return [
            {
                'report_id': r.id,
                'name': r.name,
                'original_name': r.original_name,
                'username': r.username,
                'upload_time': r.upload_time,
                'file_size': r.file_size,
            }
            for r in reports
        ]
    finally:
        session.close()

