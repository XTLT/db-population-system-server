import os
import logging
from flask import Blueprint, request, jsonify, send_file

from database import get_session, Person, add_operation_log
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name, clean_filename
from config import PHOTO_EXTENSIONS, BASE_DIR, MAX_UPLOAD_SIZE

logger = logging.getLogger('population_system')
PHOTO_UPLOAD_DIR = os.path.join(BASE_DIR, 'Photos')
os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)


bp = Blueprint('photos', __name__)


def safe_id_card_query(session, person_id: str):
    """
    安全的人员查询：先尝试ID查询，失败后尝试身份证号查询（带速率限制）
    
    Returns:
        (person, error_response) - 人员对象或错误响应
    """
    # 先尝试按ID查询
    p = session.query(Person).filter(Person.id == person_id).first()
    if p:
        return p, None
    
    # 检查是否可能是身份证号（18位数字）
    if len(person_id) == 18 and (person_id[:-1].isdigit() and person_id[-1] in '0123456789xX'):
        # 允许身份证号查询
        p = session.query(Person).filter(Person.id_card == person_id).first()
        if p:
            return p, None
    
    # 未找到
    return None, (jsonify({'error': 'Not found'}), 404)


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


@bp.route('/photo/<id_card>/<photo_type>', methods=['DELETE'])
@require_auth
def api_delete_photo_by_type(id_card, photo_type):
    """删除指定照片"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        p = session.query(Person).filter(Person.id_card == id_card).first()
        if not p:
            return jsonify({'error': '人员不存在'}), 404
        
        # 生成照片文件名
        base_name = get_photo_base_name(photo_type, p.id_card, p.social_card1, p.social_card2, p.social_card3)
        if not base_name:
            return jsonify({'error': '无法定位照片'}), 400
        
        # 查找并删除照片
        path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
        if not path or not os.path.exists(path):
            return jsonify({'error': '照片不存在'}), 404
        
        os.remove(path)
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除照片",
            f"删除 {p.name} 的 {photo_type} 照片",
            request.remote_addr,
            "Web"
        )
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@bp.route('/photo/<filename>')
@require_auth
def api_serve_photo(filename):
    """提供照片文件访问（需要认证）"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': '无效的文件名'}), 400
        
        # 检查文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 安全检查：只允许访问 Photos 目录下的文件
        file_path = os.path.join(PHOTO_UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': '照片不存在'}), 404
        
        # 检查文件是否在允许的目录内
        real_path = os.path.realpath(file_path)
        if not real_path.startswith(os.path.realpath(PHOTO_UPLOAD_DIR)):
            return jsonify({'error': '无权访问'}), 403
        
        return send_file(file_path)
    except Exception as e:
        logger.error(f"照片访问错误: {e}")
        return jsonify({'error': '服务器错误'}), 500


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


@bp.route('/photos/batch-delete', methods=['POST'])
@require_auth
def api_batch_delete_photos():
    """批量删除照片（仅管理员）"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    photos = data.get('photos', [])
    
    if not photos:
        return jsonify({'error': '未选择照片'}), 400
    
    deleted_count = 0
    not_found_count = 0
    errors = []
    
    session = get_session()
    try:
        for photo_info in photos:
            person_id = photo_info.get('person_id')
            photo_type = photo_info.get('photo_type', '身份证')
            id_card = photo_info.get('id_card')
            
            if person_id:
                # 使用 safe_id_card_query 支持身份证号查询
                p, error = safe_id_card_query(session, person_id)
                if error:
                    not_found_count += 1
                    continue
                id_card = p.id_card
                social1 = p.social_card1
                social2 = p.social_card2
                social3 = p.social_card3
            elif id_card:
                social1 = photo_info.get('social1', '')
                social2 = photo_info.get('social2', '')
                social3 = photo_info.get('social3', '')
            else:
                errors.append("缺少person_id或id_card")
                continue
            
            base_name = get_photo_base_name(photo_type, id_card, social1, social2, social3)
            if not base_name or base_name == "无":
                not_found_count += 1
                continue
            
            path = find_existing_photo(base_name, PHOTO_UPLOAD_DIR)
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"删除失败: {path} - {str(e)}")
            else:
                not_found_count += 1
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量删除照片",
            f"删除{deleted_count}张，未找到{not_found_count}张",
            request.remote_addr,
            "Web"
        )
        
        result = {
            'success': True,
            'deleted': deleted_count,
            'not_found': not_found_count
        }
        if errors:
            result['errors'] = errors
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
