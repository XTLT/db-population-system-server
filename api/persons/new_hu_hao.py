from flask import jsonify

from database import generate_new_hu_hao
from utils.security import require_auth
from . import bp


@bp.route('/household/new_number')
@require_auth
def api_new_hu_hao():
    """获取新户号"""
    return jsonify({'hu_hao': generate_new_hu_hao()})
