import os
from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name
from . import bp, PHOTO_UPLOAD_DIR


@bp.route('/photos/<id_card>')
@require_auth
def api_get_person_photos(id_card):
    """获取某人的所有照片"""
    session = get_session()
    try:
        p = session.query(Person).filter(Person.id_card == id_card).first()
        if not p:
            return jsonify({'error': '人员不存在'}), 404
        
        # 照片类型列表
        photo_types = ['身份证', '社保卡1', '社保卡2', '社保卡3']
        photos = []
        
        for photo_type in photo_types:
            base_name = get_photo_base_name(photo_type, p.id_card, p.social_card1, p.social_card2, p.social_card3)
            if base_name:
                path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
                if path and os.path.exists(path):
                    photos.append({
                        'photo_type': photo_type,
                        'url': f'/api/photo/{os.path.basename(path)}',
                        'file_name': os.path.basename(path),
                        'exists': True
                    })
        
        return jsonify({'photos': photos})
    finally:
        session.close()
