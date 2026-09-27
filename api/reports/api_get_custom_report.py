from flask import request, jsonify

from database import get_custom_report
from utils.security import require_auth
from . import bp


@bp.route('/custom/<report_id>')
@require_auth
def api_get_custom_report(report_id):
    """获取报表详情"""
    user = request.current_user

    try:
        report = get_custom_report(report_id)
        if not report:
            return jsonify({'error': '报表不存在'}), 404

        # 权限检查：普通用户只能查看自己的报表
        if user.get('role') != 'admin' and report['user_id'] != user['id']:
            return jsonify({'error': '权限不足'}), 403

        return jsonify({'report': report})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
