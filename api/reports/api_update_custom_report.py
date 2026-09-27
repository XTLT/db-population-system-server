from flask import request, jsonify

from database import get_custom_report, update_custom_report, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/custom/<report_id>', methods=['PUT'])
@require_auth
def api_update_custom_report(report_id):
    """更新报表"""
    user = request.current_user
    data, err = get_json_data()
    if err:
        return err

    try:
        # 先检查报表是否存在及权限
        existing = get_custom_report(report_id)
        if not existing:
            return jsonify({'error': '报表不存在'}), 404

        if user.get('role') != 'admin' and existing['user_id'] != user['id']:
            return jsonify({'error': '权限不足'}), 403

        # 验证报表类型
        if 'report_type' in data and data['report_type'] not in ['person', 'student', 'subsidy']:
            return jsonify({'error': '无效的报表类型'}), 400

        # 验证图表类型
        if 'chart_type' in data and data['chart_type'] not in ['bar', 'line', 'pie', 'radar']:
            data['chart_type'] = 'bar'

        updated = update_custom_report(report_id, **data)

        add_operation_log(
            user['id'],
            user['username'],
            "更新自定义报表",
            f"ID:{report_id}",
            request.remote_addr,
            "Web"
        )

        return jsonify({'success': True, 'report': updated})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
