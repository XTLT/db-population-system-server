from flask import request, jsonify

from database import add_operation_log
from utils.security import require_auth
from excel_importer import backup_database
from . import bp


@bp.route('', methods=['POST'])
@require_auth
def api_backup():
    """创建备份（仅管理员）"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    result = backup_database(manual=True)
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "数据备份",
        f"成功:{result.get('success', False)}",
        request.remote_addr,
        "Web"
    )
    return jsonify(result)
