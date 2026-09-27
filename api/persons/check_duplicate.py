from flask import request, jsonify

from database import check_duplicate_id_card
from utils.security import require_auth
from . import bp


@bp.route('/check_duplicate')
@require_auth
def api_check_duplicate():
    """检查身份证号是否重复"""
    hu_hao = request.args.get('hu_hao', '')
    id_card = request.args.get('id_card', '')
    if not hu_hao or not id_card:
        return jsonify({'duplicate': False})
    duplicate = check_duplicate_id_card(hu_hao, id_card)
    return jsonify({'duplicate': duplicate})
