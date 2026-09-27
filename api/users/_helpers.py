from flask import request


def _require_admin():
    """检查是否为管理员"""
    if request.current_user.get('role') != 'admin':
        return False
    return True
