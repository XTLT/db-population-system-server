import os
from flask import request, jsonify

from database import get_session, Person
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name, clean_filename
from config import PHOTO_EXTENSIONS, MAX_UPLOAD_SIZE
from . import bp, PHOTO_UPLOAD_DIR


@bp.route('/upload_photo', methods=['POST'])
@require_auth
def api_upload_photo_by_id_card():
    """通过身份证号上传照片"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    # 获取参数
    id_card = request.form.get('id_card', '')
    photo_type = request.form.get('photo_type', '身份证')
    
    if not id_card:
        return jsonify({'error': '身份证号不能为空'}), 400
    
    if 'photo' not in request.files and 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    # 获取文件（兼容两种字段名）
    file = request.files.get('photo') or request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': '未选择文件'}), 400
    
    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_UPLOAD_SIZE:
        return jsonify({'error': f'文件大小超过限制（最大 {MAX_UPLOAD_SIZE // (1024*1024)}MB）'}), 400
    
    # 检查文件格式
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in PHOTO_EXTENSIONS:
        return jsonify({'error': f'不支持的文件格式，仅支持：{", ".join(PHOTO_EXTENSIONS)}'}), 400
    
    # 查找人员
    session = get_session()
    try:
        p = session.query(Person).filter(Person.id_card == id_card).first()
        if not p:
            return jsonify({'error': '人员不存在'}), 404
        
        # 生成照片文件名
        base_name = get_photo_base_name(photo_type, p.id_card, p.social_card1, p.social_card2, p.social_card3)
        if not base_name:
            return jsonify({'error': '无法生成照片文件名'}), 400
        
        # 清理文件名并删除旧照片
        cleaned = clean_filename(base_name)
        old = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
        if old and os.path.exists(old):
            os.remove(old)
        
        # 保存新照片
        dest = os.path.join(PHOTO_UPLOAD_DIR, cleaned + ext)
        file.save(dest)
        
        # 返回照片URL
        photo_url = f'/api/photo/{cleaned}{ext}'
        
        return jsonify({
            'success': True,
            'url': photo_url,
            'message': '上传成功'
        })
    finally:
        session.close()
