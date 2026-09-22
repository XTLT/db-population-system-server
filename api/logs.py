from datetime import datetime
from flask import Blueprint, request, jsonify

from database import get_operation_logs, get_operation_types, get_operation_log_stats
from utils.security import require_auth


bp = Blueprint('logs', __name__)


def validate_date(date_str):
    """验证日期格式是否为 YYYY-MM-DD"""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


@bp.route('/')
@require_auth
def api_logs():
    """
    获取操作日志列表
    
    Query Parameters:
        limit: 返回记录数量，默认100
        username: 用户名筛选（可选）
        operation_type: 操作类型筛选（可选）
        start_date: 开始日期，格式 YYYY-MM-DD（可选）
        end_date: 结束日期，格式 YYYY-MM-DD（可选）
    """
    user = request.current_user
    is_admin = user.get('role') == 'admin'
    username = user.get('username', '')
    
    # 验证 limit 参数
    limit = min(max(request.args.get('limit', 100, type=int), 1), 1000)
    
    filter_username = request.args.get('username', '')
    filter_operation_type = request.args.get('operation_type', '')
    filter_start_date = request.args.get('start_date', '')
    filter_end_date = request.args.get('end_date', '')
    
    # 验证日期格式
    if filter_start_date and not validate_date(filter_start_date):
        return jsonify({'error': '开始日期格式错误，应为 YYYY-MM-DD'}), 400
    
    if filter_end_date and not validate_date(filter_end_date):
        return jsonify({'error': '结束日期格式错误，应为 YYYY-MM-DD'}), 400
    
    # 权限控制：普通用户只能查看自己的日志
    if not is_admin:
        filter_username = username  # 强制使用当前用户
    
    # 调用查询函数
    logs = get_operation_logs(
        limit=limit,
        username=filter_username if filter_username else None,
        operation_type=filter_operation_type if filter_operation_type else None,
        start_date=filter_start_date if filter_start_date else None,
        end_date=filter_end_date if filter_end_date else None
    )
    
    return jsonify([{
        'id': l.id,
        'username': l.username,
        'operation_type': l.operation_type,
        'operation_target': l.operation_target,
        'ip_address': l.ip_address,
        'client_type': l.client_type,
        'created_at': l.created_at,
        'is_high_risk': l.is_high_risk
    } for l in logs])


@bp.route('/types')
@require_auth
def api_log_types():
    """获取操作类型列表"""
    types = get_operation_types()
    return jsonify({'types': types})


@bp.route('/stats')
@require_auth
def api_log_stats():
    """获取操作日志统计信息（仅管理员）"""
    user = request.current_user
    is_admin = user.get('role') == 'admin'
    
    if not is_admin:
        return jsonify({'error': '权限不足'}), 403
    
    stats = get_operation_log_stats()
    return jsonify(stats)
