"""update_custom_report 函数。"""

from ..models.custom_report import CustomReport
from .._base import get_session

def update_custom_report(report_id: str, **kwargs) -> dict | None:
    from datetime import datetime
    import json
    
    session = get_session()
    try:
        report = session.query(CustomReport).filter(CustomReport.id == report_id).first()
        if not report:
            return None
        
        # 处理 JSON 字段
        if 'dimensions' in kwargs and isinstance(kwargs['dimensions'], list):
            kwargs['dimensions'] = json.dumps(kwargs['dimensions'], ensure_ascii=False)
        if 'date_range' in kwargs and isinstance(kwargs['date_range'], dict):
            kwargs['date_range'] = json.dumps(kwargs['date_range'], ensure_ascii=False)
        if 'filters' in kwargs and isinstance(kwargs['filters'], dict):
            kwargs['filters'] = json.dumps(kwargs['filters'], ensure_ascii=False)
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        
        report.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        
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
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

