"""get_custom_report 函数。"""

from ..models.custom_report import CustomReport
from .._base import get_session

def get_custom_report(report_id: str) -> dict | None:
    import json
    
    session = get_session()
    try:
        report = session.query(CustomReport).filter(CustomReport.id == report_id).first()
        if not report:
            return None
        
        return {
            "id": report.id,
            "title": report.title,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "dimensions": json.loads(report.dimensions) if report.dimensions else [],
            "date_range": json.loads(report.date_range) if report.date_range else {},
            "chart_type": report.chart_type,
            "filters": json.loads(report.filters) if report.filters else {},
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    finally:
        session.close()

