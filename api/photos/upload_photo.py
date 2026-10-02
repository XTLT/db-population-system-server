import os
from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name, clean_filename
from config import PHOTO_EXTENSIONS, MAX_UPLOAD_SIZE
from . import bp, PHOTO_UPLOAD_DIR
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/photo', methods=['POST'])
@require_auth
def api_upload_photo(person_id):
    """上传照片"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        # 使用 safe_id_card_query 支持身份证号查询
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        photo_type = request.form.get('photo_type', '身份证')
        if 'file' not in request.files:
            return jsonify({'error': '未选择文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'error': '未选择文件'}), 400

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_UPLOAD_SIZE:
            return jsonify({'error': f'文件大小超过限制（最大 {MAX_UPLOAD_SIZE // (1024*1024)}MB）'}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in PHOTO_EXTENSIONS:
            return jsonify({'error': f'不支持的文件格式，仅支持：{", ".join(PHOTO_EXTENSIONS)}'}), 400

        base_name = get_photo_base_name(photo_type, p.id_card, p.social_card1, p.social_card2, p.social_card3)
        if not base_name:
            return jsonify({'error': '无法生成照片文件名'}), 400

        cleaned = clean_filename(base_name)
        old = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
        if old and os.path.exists(old):
            os.remove(old)

        dest = os.path.join(PHOTO_UPLOAD_DIR, cleaned + ext)
        file.save(dest)

        # 返回照片访问URL
        photo_url = f'/api/person/{p.id_card}/photo'

        return jsonify({
            'success': True,
            'url': photo_url,
            'message': '上传成功'
        })
    finally:
        session.close()
