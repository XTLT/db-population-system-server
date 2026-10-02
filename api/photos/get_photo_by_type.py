import os
from flask import request, jsonify, send_file

from database import get_session, Person
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name
from . import bp, PHOTO_UPLOAD_DIR


@bp.route('/photo/<id_card>/<photo_type>')
@require_auth
def api_get_photo_by_type(id_card, photo_type):
    """获取指定类型的照片（移动端使用）"""
    session = get_session()
    try:
        p = session.query(Person).filter(Person.id_card == id_card).first()
        if not p:
            return jsonify({'error': '人员不存在'}), 404
        
        # 根据照片类型生成文件名
        base_name = get_photo_base_name(photo_type, p.id_card, p.social_card1, p.social_card2, p.social_card3)
        if not base_name:
            return jsonify({'error': '无法定位照片'}), 400
        
        # 查找照片文件
        path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
        if path and os.path.exists(path):
            return send_file(path, mimetype='image/jpeg')
        
        return jsonify({'error': '照片不存在'}), 404
    finally:
        session.close()
