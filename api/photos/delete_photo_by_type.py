import os
from flask import request, jsonify

from database import get_session, Person, add_operation_log
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name
from . import bp, PHOTO_UPLOAD_DIR


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
