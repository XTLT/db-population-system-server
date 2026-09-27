"""get_person_trend_data 函数。"""

from ..models.operation_log import OperationLog
from ..models.deleted_person import DeletedPerson
from .._base import get_session

def get_person_trend_data(start_date: str, end_date: str, group_by: str = 'month') -> dict:
    from datetime import datetime, timedelta
    
    session = get_session()
    try:
        # 解析日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now() - timedelta(days=365)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
        
        # 生成时间标签
        labels = []
        current = start_dt
        while current <= end_dt:
            if group_by == 'day':
                labels.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            elif group_by == 'week':
                # 按周分组（使用周一日期）
                week_start = current - timedelta(days=current.weekday())
                labels.append(week_start.strftime('%Y-%m-%d'))
                current += timedelta(weeks=1)
            elif group_by == 'month':
                labels.append(current.strftime('%Y-%m'))
                # 移动到下个月
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)
            elif group_by == 'year':
                labels.append(current.strftime('%Y'))
                current = current.replace(year=current.year + 1, day=1)
            else:
                labels.append(current.strftime('%Y-%m'))
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)
        
        # 统计新增人员（通过操作日志）
        addition_counts = {label: 0 for label in labels}
        additions = session.query(OperationLog).filter(
            OperationLog.operation_type == "添加人员",
            OperationLog.created_at >= start_dt.strftime('%Y-%m-%d'),
            OperationLog.created_at <= end_dt.strftime('%Y-%m-%d') + ' 23:59:59'
        ).all()
        
        for log in additions:
            if log.created_at:
                date_str = log.created_at.split()[0]  # 取日期部分
                try:
                    log_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    if group_by == 'day':
                        key = log_dt.strftime('%Y-%m-%d')
                    elif group_by == 'week':
                        week_start = log_dt - timedelta(days=log_dt.weekday())
                        key = week_start.strftime('%Y-%m-%d')
                    elif group_by == 'month':
                        key = log_dt.strftime('%Y-%m')
                    elif group_by == 'year':
                        key = log_dt.strftime('%Y')
                    else:
                        key = log_dt.strftime('%Y-%m')
                    
                    if key in addition_counts:
                        addition_counts[key] += 1
                except Exception:
                    pass
        
        # 统计删除人员
        deletion_counts = {label: 0 for label in labels}
        deletions = session.query(DeletedPerson).filter(
            DeletedPerson.deleted_at >= start_dt.strftime('%Y-%m-%d'),
            DeletedPerson.deleted_at <= end_dt.strftime('%Y-%m-%d') + ' 23:59:59'
        ).all()
        
        for deleted in deletions:
            if deleted.deleted_at:
                date_str = deleted.deleted_at.split()[0] if ' ' in deleted.deleted_at else deleted.deleted_at
                try:
                    del_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    if group_by == 'day':
                        key = del_dt.strftime('%Y-%m-%d')
                    elif group_by == 'week':
                        week_start = del_dt - timedelta(days=del_dt.weekday())
                        key = week_start.strftime('%Y-%m-%d')
                    elif group_by == 'month':
                        key = del_dt.strftime('%Y-%m')
                    elif group_by == 'year':
                        key = del_dt.strftime('%Y')
                    else:
                        key = del_dt.strftime('%Y-%m')
                    
                    if key in deletion_counts:
                        deletion_counts[key] += 1
                except Exception:
                    pass
        
        return {
            'labels': labels,
            'additions': [addition_counts.get(label, 0) for label in labels],
            'deletions': [deletion_counts.get(label, 0) for label in labels],
            'total_additions': sum(addition_counts.values()),
            'total_deletions': sum(deletion_counts.values())
        }
    finally:
        session.close()

