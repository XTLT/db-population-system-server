import os
from flask import request, jsonify

from database import get_session, add_operation_log
from utils.security import require_auth
from utils import find_existing_photo, get_photo_base_name
from . import bp, PHOTO_UPLOAD_DIR
from ._helpers import safe_id_card_query


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
