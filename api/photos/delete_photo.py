import os
from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name
from . import bp, PHOTO_UPLOAD_DIR
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/photo', methods=['DELETE'])
@require_auth
def api_delete_photo(person_id):
    """删除照片"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        photo_type = request.args.get('photo_type', '身份证')
        base_name = get_photo_base_name(photo_type, p.id_card, p.social_card1, p.social_card2, p.social_card3)
        if not base_name:
            return jsonify({'error': '无法生成照片文件名'}), 400

        path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
        if path and os.path.exists(path):
            os.remove(path)
            return jsonify({'success': True})

        return jsonify({'error': '照片不存在'}), 404
    finally:
        session.close()
