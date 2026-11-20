"""读取数据库密码（优先内存，其次系统密钥环）。"""


def get_db_password() -> str:
    from .. import _base

    if _base._db_password:
        return _base._db_password
    try:
        import keyring
        pw = keyring.get_password(_base.SERVICE_NAME, "db_password")
        if pw:
            _base._db_password = pw
            return pw
    except Exception as e:
        _base.logger.warning(f"无法从系统密钥环读取密码: {e}")
    return ""
