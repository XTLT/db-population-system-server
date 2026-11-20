"""获取一个数据库会话（调用方负责 close）。"""

from .get_engine import get_engine


def get_session():
    from .. import _base

    if _base._SessionFactory is None:
        from sqlalchemy.orm import sessionmaker
        _base._SessionFactory = sessionmaker(bind=get_engine())
    return _base._SessionFactory()
