"""get_custom_reports 函数。"""

from ..models.custom_report import CustomReport
from .._base import get_session

def get_custom_reports(user_id: str = None, report_type: str = None, limit: int = 50) -> list:
    import json
    
    session = get_session()
    try:
        query = session.query(CustomReport)
        
        if user_id:
            query = query.filter(CustomReport.user_id == user_id)
        
        if report_type:
            query = query.filter(CustomReport.report_type == report_type)
        
        reports = query.order_by(CustomReport.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "title": r.title,
                "user_id": r.user_id,
                "report_type": r.report_type,
                "dimensions": json.loads(r.dimensions) if r.dimensions else [],
                "date_range": json.loads(r.date_range) if r.date_range else {},
                "chart_type": r.chart_type,
                "filters": json.loads(r.filters) if r.filters else {},
                "created_at": r.created_at,
                "updated_at": r.updated_at
            }
            for r in reports
        ]
    finally:
        session.close()

