from flask import Blueprint, request, jsonify

from database import (
    create_custom_report,
    get_custom_reports,
    get_custom_report,
    update_custom_report,
    delete_custom_report,
    generate_report_data,
    add_operation_log
)
from utils.security import require_auth
from utils.response import get_json_data


bp = Blueprint('reports', __name__)


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


@bp.route('/custom/<report_id>', methods=['DELETE'])
@require_auth
def api_delete_custom_report(report_id):
    """删除报表"""
    user = request.current_user
    
    try:
        # 先检查报表是否存在及权限
        existing = get_custom_report(report_id)
        if not existing:
            return jsonify({'error': '报表不存在'}), 404
        
        if user.get('role') != 'admin' and existing['user_id'] != user['id']:
            return jsonify({'error': '权限不足'}), 403
        
        deleted = delete_custom_report(report_id)
        
        if deleted:
            add_operation_log(
                user['id'],
                user['username'],
                "删除自定义报表",
                f"ID:{report_id}, 标题:{existing['title']}",
                request.remote_addr,
                "Web"
            )
            return jsonify({'success': True})
        else:
            return jsonify({'error': '删除失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
