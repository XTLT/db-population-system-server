from flask import request, jsonify

from database import generate_report_data, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/generate', methods=['POST'])
@require_auth
def api_generate_report():
    """生成报表数据（预览）"""
    user = request.current_user
    data, err = get_json_data()
    if err:
        return err

    report_type = data.get('report_type', '')
    dimensions = data.get('dimensions', [])
    date_range = data.get('date_range', {})
    filters = data.get('filters', {})

    if report_type not in ['person', 'student', 'subsidy']:
        return jsonify({'error': '无效的报表类型，支持: person, student, subsidy'}), 400

    if not dimensions:
        return jsonify({'error': '请选择至少一个统计维度'}), 400

    try:
        result = generate_report_data(
            report_type=report_type,
            dimensions=dimensions,
            date_range=date_range,
            filters=filters
        )

        add_operation_log(
            user['id'],
            user['username'],
            "生成报表数据",
            f"类型:{report_type}, 维度:{','.join(dimensions)}",
            request.remote_addr,
            "Web"
        )

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
