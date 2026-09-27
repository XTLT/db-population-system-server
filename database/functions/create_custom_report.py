"""create_custom_report 函数。"""

import secrets
from ..models.custom_report import CustomReport
from .._base import get_session

def create_custom_report(user_id: str, title: str, report_type: str, 
                         dimensions: list = None, date_range: dict = None,
                         chart_type: str = "bar", filters: dict = None) -> dict:
    from datetime import datetime
    import json
    
    session = get_session()
    try:
        report = CustomReport(
            id=f"report_{secrets.token_hex(8)}",
            title=title,
            user_id=user_id,
            report_type=report_type,
            dimensions=json.dumps(dimensions or [], ensure_ascii=False),
            date_range=json.dumps(date_range or {}, ensure_ascii=False),
            chart_type=chart_type,
            filters=json.dumps(filters or {}, ensure_ascii=False),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=""
        )
        session.add(report)
        session.commit()
        
        return {
            "id": report.id,
            "title": report.title,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "dimensions": json.loads(report.dimensions),
            "date_range": json.loads(report.date_range),
            "chart_type": report.chart_type,
            "filters": json.loads(report.filters),
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

