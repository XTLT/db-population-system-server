"""create_report_file 函数。"""

from ..models.report_file import ReportFile
from .._base import get_session

def create_report_file(name: str, original_name: str, stored_filename: str,
                       file_path: str, file_size: int, user_id: str, username: str) -> dict:
    from datetime import datetime
    import uuid
    session = get_session()
    try:
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = ReportFile(
            id=report_id,
            name=name,
            original_name=original_name,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            upload_user_id=user_id,
            username=username,
            upload_time=now,
            created_at=now,
        )
        session.add(report)
        session.commit()
        return {
            'report_id': report_id,
            'name': name,
            'original_name': original_name,
            'username': username,
            'upload_time': now,
            'file_size': file_size,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

