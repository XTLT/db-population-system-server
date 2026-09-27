from flask import jsonify

from database import get_report_files
from utils.security import require_auth
from . import bp


@bp.route('', methods=['GET'])
@require_auth
def api_list_reports():
    """获取报表文件列表"""
    reports = get_report_files()
    return jsonify(reports)
