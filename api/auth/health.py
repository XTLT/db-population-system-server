from flask import jsonify

from . import bp


@bp.route('/health')
def api_health():
    """健康检查端点（移动端域名检查使用）"""
    return jsonify({'status': 'ok', 'healthy': True})
