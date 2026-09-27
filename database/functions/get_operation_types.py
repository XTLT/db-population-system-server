"""get_operation_types 函数。"""

from ..models.operation_log import OperationLog
from .._base import get_session

def get_operation_types() -> list:
    session = get_session()
    try:
        result = session.query(
            OperationLog.operation_type
        ).distinct().order_by(OperationLog.operation_type).all()
        return [r[0] for r in result if r[0]]
    finally:
        session.close()

