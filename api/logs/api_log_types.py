from flask import jsonify

from database import get_operation_types
from utils.security import require_auth
from . import bp


@bp.route('/types')
@require_auth
def api_log_types():
    """获取操作类型列表"""
    types = get_operation_types()
    return jsonify({'types': types})
