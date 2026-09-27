from flask import request, jsonify

from database import create_custom_report, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/custom', methods=['POST'])
@require_auth
def api_create_custom_report():
    """创建自定义报表"""
    user = request.current_user
    data, err = get_json_data()
    if err:
        return err

    title = data.get('title', '').strip()
    report_type = data.get('report_type', '')
    dimensions = data.get('dimensions', [])
    date_range = data.get('date_range', {})
    chart_type = data.get('chart_type', 'bar')
    filters = data.get('filters', {})

    if not title:
        return jsonify({'error': '报表标题不能为空'}), 400

    if report_type not in ['person', 'student', 'subsidy']:
        return jsonify({'error': '无效的报表类型，支持: person, student, subsidy'}), 400

    if chart_type not in ['bar', 'line', 'pie', 'radar']:
        chart_type = 'bar'

    try:
        report = create_custom_report(
            user_id=user['id'],
            title=title,
            report_type=report_type,
            dimensions=dimensions,
            date_range=date_range,
            chart_type=chart_type,
            filters=filters
        )

        add_operation_log(
            user['id'],
            user['username'],
            "创建自定义报表",
            f"标题:{title}, 类型:{report_type}",
            request.remote_addr,
            "Web"
        )

        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
