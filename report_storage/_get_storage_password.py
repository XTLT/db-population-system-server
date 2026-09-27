def _get_storage_password():
    from database import get_db_password
    pw = get_db_password()
    if pw:
        return pw
    return "default_report_key"
