"""get_report_file 函数。"""

from ..models.report_file import ReportFile
from .._base import get_session

def get_report_file(report_id: str) -> dict:
    session = get_session()
    try:
        r = session.query(ReportFile).filter(ReportFile.id == report_id).first()
        if not r:
            return None
        return {
            'report_id': r.id,
            'name': r.name,
            'original_name': r.original_name,
            'stored_filename': r.stored_filename,
            'file_path': r.file_path,
            'file_size': r.file_size,
            'upload_user_id': r.upload_user_id,
            'username': r.username,
            'upload_time': r.upload_time,
        }
    finally:
        session.close()

