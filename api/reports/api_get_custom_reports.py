from flask import request, jsonify

from database import get_custom_reports
from utils.security import require_auth
from . import bp


@bp.route('/custom')
@require_auth
def api_get_custom_reports():
    """获取报表列表"""
    user = request.current_user
    report_type = request.args.get('report_type', '')
    limit = request.args.get('limit', 50, type=int)

    # 普通用户只能看自己的报表，管理员可以看到所有
    user_id = None if user.get('role') == 'admin' else user['id']

    try:
        reports = get_custom_reports(user_id=user_id, report_type=report_type, limit=limit)
        return jsonify({'reports': reports})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
