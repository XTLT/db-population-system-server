import os
from flask import request, jsonify, send_file

from database import get_session, Person
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name
from . import bp, PHOTO_UPLOAD_DIR
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/photo')
@require_auth
def api_get_photo(person_id):
    """获取照片"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        base_name = get_photo_base_name('身份证', p.id_card, p.social_card1, p.social_card2, p.social_card3)
        if not base_name:
            return jsonify({'error': '无法查找照片'}), 400

        path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
        if path and os.path.exists(path):
            return send_file(path, mimetype='image/jpeg')

        for card in [p.social_card1, p.social_card2, p.social_card3]:
            if card and card != "无":
                base = get_photo_base_name('身份证', card, '', '', '')
                if base:
                    path = find_existing_photo(base, PHOTO_UPLOAD_DIR)
                    if path and os.path.exists(path):
                        return send_file(path, mimetype='image/jpeg')

        return jsonify({'error': '照片不存在'}), 404
    finally:
        session.close()
