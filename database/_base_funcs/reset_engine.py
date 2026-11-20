"""释放并清空 engine 与 session 工厂（改密码、加解密后必须重建）。"""


def reset_engine():
    from .. import _base

    if _base._engine is not None:
        _base._engine.dispose()
    _base._engine = None
    _base._SessionFactory = None
