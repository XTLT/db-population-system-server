"""purge_deleted_persons 函数：物理清理超过指定天数的已删除人员记录。"""

from datetime import datetime, timedelta
from ..models.deleted_person import DeletedPerson
from .._base import get_session


def purge_deleted_persons(days: int = 90) -> int:
    """物理删除 deleted_at 早于 days 天前的已删除记录，返回删除条数。

    注意：物理删除不可恢复，默认保留 90 天，调用方应显式确认。
    """
    session = get_session()
    try:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        count = session.query(DeletedPerson).filter(
            DeletedPerson.deleted_at < cutoff
        ).delete(synchronize_session=False)
        session.commit()
        return count
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
