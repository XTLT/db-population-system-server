import os
from flask import request, jsonify

from database import get_report_file, delete_report_file, add_report_log
from utils.security import require_auth
from . import bp


@bp.route('/<report_id>', methods=['DELETE'])
@require_auth
def api_delete_report(report_id):
    """删除报表"""
    user = request.current_user
    report = get_report_file(report_id)
    if not report:
        return jsonify({'error': '报表不存在'}), 404

    if os.path.exists(report['file_path']):
        try:
            os.remove(report['file_path'])
        except OSError:
            pass

    delete_report_file(report_id)

    add_report_log(
        report_id=report_id,
        user_id=user['id'],
        username=user['username'],
        operation_type='删除报表',
        operation_detail=f'文件:{report["original_name"]}',
        ip_address=request.remote_addr,
        client_type='Desktop',
    )

    return jsonify({'success': True})
