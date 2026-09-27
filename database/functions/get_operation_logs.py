"""get_operation_logs 函数。"""

from ..models.operation_log import OperationLog
from .._base import get_session

def get_operation_logs(limit: int = 100, username: str = None, operation_type: str = None, start_date: str = None, end_date: str = None) -> list:
    session = get_session()
    try:
        query = session.query(OperationLog)
        
        # 应用筛选条件
        if username:
            query = query.filter(OperationLog.username == username)
        
        if operation_type:
            query = query.filter(OperationLog.operation_type == operation_type)
        
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        
        if end_date:
            # 结束日期包含当天的所有记录
            end_datetime = f"{end_date} 23:59:59"
            query = query.filter(OperationLog.created_at <= end_datetime)
        
        # 按时间倒序排列
        query = query.order_by(OperationLog.created_at.desc())
        
        # 限制返回数量
        return query.limit(limit).all()
    finally:
        session.close()

