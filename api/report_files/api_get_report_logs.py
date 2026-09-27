from flask import jsonify

from database import get_report_file, get_report_logs
from utils.security import require_auth
from . import bp


@bp.route('/<report_id>/logs')
@require_auth
def api_get_report_logs(report_id):
    """获取报表操作日志"""
    report = get_report_file(report_id)
    if not report:
        return jsonify({'error': '报表不存在'}), 404

    logs = get_report_logs(report_id)
    return jsonify({'db_logs': logs, 'file_logs': []})
