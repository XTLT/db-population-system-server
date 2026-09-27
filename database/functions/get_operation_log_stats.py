"""get_operation_log_stats 函数。"""

from ..models.operation_log import OperationLog
from .._base import get_session

def get_operation_log_stats() -> dict:
    session = get_session()
    try:
        from sqlalchemy import func
        from datetime import date
        
        # 总记录数
        total = session.query(func.count(OperationLog.id)).scalar()
        
        # 今日记录数
        today_str = date.today().strftime("%Y-%m-%d")
        today = session.query(func.count(OperationLog.id)).filter(
            OperationLog.created_at >= today_str
        ).scalar()
        
        # 高风险操作数
        high_risk = session.query(func.count(OperationLog.id)).filter(
            OperationLog.is_high_risk == "是"
        ).scalar()
        
        # 按操作类型统计（前10）
        by_type_result = session.query(
            OperationLog.operation_type,
            func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.operation_type).order_by(
            func.count(OperationLog.id).desc()
        ).limit(10).all()
        
        by_type = {r[0]: r[1] for r in by_type_result}
        
        # 按用户统计（前5）
        by_user_result = session.query(
            OperationLog.username,
            func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.username).order_by(
            func.count(OperationLog.id).desc()
        ).limit(5).all()
        
        by_user = {r[0]: r[1] for r in by_user_result}
        
        return {
            'total': total or 0,
            'today': today or 0,
            'high_risk': high_risk or 0,
            'by_type': by_type,
            'by_user': by_user
        }
    finally:
        session.close()

