"""GET /api/photos/manifest-all：返回全部人员已有照片的清单。

移动端下载离线全量包时先取本清单，再按 url 逐张下载到本机缓存。
不直接打包照片，避免单次响应过大；旧客户端不会调用本接口。
"""

import os
from datetime import datetime

from flask import jsonify

from database import Person, get_session
from utils import find_existing_photo, get_photo_base_name
from utils.security import require_auth
from . import bp, PHOTO_UPLOAD_DIR

PHOTO_TYPES = ('身份证', '社保卡1', '社保卡2', '社保卡3')


@bp.route('/photos/manifest-all')
@require_auth
def api_photos_manifest_all():
    session = get_session()
    try:
        persons = session.query(Person).all()
        photos = []
        for p in persons:
            id_card = (p.id_card or '').strip()
            if not id_card:
                continue
            for photo_type in PHOTO_TYPES:
                base_name = get_photo_base_name(
                    photo_type,
                    p.id_card,
                    p.social_card1,
                    p.social_card2,
                    p.social_card3,
                )
                if not base_name:
                    continue
                path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
                if not path or not os.path.exists(path):
                    continue
                file_name = os.path.basename(path)
                try:
                    stat = os.stat(path)
                    size = stat.st_size
                    modified_at = datetime.fromtimestamp(stat.st_mtime).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )
                except OSError:
                    size = 0
                    modified_at = ''
                photos.append({
                    'id_card': id_card,
                    'name': p.name or '',
                    'photo_type': photo_type,
                    'url': f'/api/photo/{file_name}',
                    'file_name': file_name,
                    'size': size,
                    'modified_at': modified_at,
                })
        return jsonify({'photos': photos, 'total': len(photos)})
    finally:
        session.close()
