from flask import request, jsonify

from utils.security import require_auth
from excel_importer import get_backup_list
from . import bp


@bp.route('/list')  # /api/backup/list
@require_auth
def api_backup_list():
    """获取备份列表（仅管理员）"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    backups = get_backup_list()
    return jsonify({'backups': backups})
