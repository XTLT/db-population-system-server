import os
from flask import request, jsonify, send_file

from database import get_report_file, add_report_log
from utils.security import require_auth
from . import bp


@bp.route('/<report_id>/download')
@require_auth
def api_download_report(report_id):
    """下载报表文件"""
    report = get_report_file(report_id)
    if not report:
        return jsonify({'error': '报表不存在'}), 404

    if not os.path.exists(report['file_path']):
        return jsonify({'error': '文件不存在'}), 404

    user = request.current_user
    add_report_log(
        report_id=report_id,
        user_id=user['id'],
        username=user['username'],
        operation_type='下载报表',
        operation_detail=f'文件:{report["original_name"]}',
        ip_address=request.remote_addr,
        client_type='Desktop',
    )

    return send_file(
        report['file_path'],
        as_attachment=True,
        download_name=report['original_name'],
    )
