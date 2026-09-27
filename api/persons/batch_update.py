from datetime import datetime
from flask import request, jsonify

from database import get_session, Person, add_operation_log
from utils.security import require_auth
from utils.response import safe_exception
from . import bp
from ._batch_constants import MAX_BATCH_UPDATE_COUNT, BATCH_UPDATE_ALLOWED_FIELDS


@bp.route('/persons/batch-update', methods=['POST'])
@require_auth
def api_batch_update_persons():
    """批量更新人员信息（仅管理员）
    
    安全限制：
    - 单次最多更新 200 条记录
    - 只允许更新白名单中的字段
    - 验证更新值的有效性
    """
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    person_ids = data.get('ids', [])
    updates = data.get('updates', {})
    
    if not person_ids:
        return jsonify({'error': '未选择人员'}), 400
    
    if not updates:
        return jsonify({'error': '未提供更新内容'}), 400
    
    # 数量限制
    if len(person_ids) > MAX_BATCH_UPDATE_COUNT:
        return jsonify({
            'error': f'单次最多更新 {MAX_BATCH_UPDATE_COUNT} 条记录，当前选择了 {len(person_ids)} 条'
        }), 400
    
    # 过滤不允许更新的字段
    filtered_updates = {}
    for key, value in updates.items():
        if key in BATCH_UPDATE_ALLOWED_FIELDS:
            filtered_updates[key] = value
    
    if not filtered_updates:
        return jsonify({'error': '没有有效的更新字段'}), 400
    
    session = get_session()
    try:
        persons = session.query(Person).filter(Person.id.in_(person_ids)).all()
        updated_count = 0
        
        for person in persons:
            for key, value in filtered_updates.items():
                setattr(person, key, value)
            person.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量更新人员",
            f"更新{updated_count}人，字段: {','.join(filtered_updates.keys())}",
            request.remote_addr,
            "Web"
        )
        
        return jsonify({'success': True, 'updated': updated_count, 'fields_updated': list(filtered_updates.keys())})
    except Exception as e:
        session.rollback()
        return safe_exception(e, "更新失败", 500)
    finally:
        session.close()
