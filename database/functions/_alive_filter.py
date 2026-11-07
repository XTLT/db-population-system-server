"""人员表“在世”筛选条件，与统计页 statistics.py 保持同一口径。"""
from ..models.person import Person


def alive_filter():
    """排除 is_dead='是' 的人员（NULL 视为在世）。"""
    return (Person.is_dead != "是") | (Person.is_dead.is_(None))
