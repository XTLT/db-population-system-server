from flask import jsonify

from utils.security import require_auth
from excel_importer import get_backup_status
from . import bp


@bp.route('/status')
@require_auth
def api_backup_status():
    """获取备份状态"""
    status = get_backup_status()
    return jsonify(status)
