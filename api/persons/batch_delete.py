from flask import request, jsonify

from database import get_session, Person, add_operation_log
from utils.security import require_auth
from utils.response import safe_exception
from . import bp
from ._batch_constants import MAX_BATCH_DELETE_COUNT


@bp.route('/persons/batch-delete', methods=['POST'])
@require_auth
def api_batch_delete_persons():
    """批量删除人员（仅管理员）
    
    安全限制：
    - 单次最多删除 100 条记录
    - 需要管理员权限
    - 记录详细审计日志
    """
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    person_ids = data.get('ids', [])
    
    if not person_ids:
        return jsonify({'error': '未选择人员'}), 400
    
    # 数量限制
    if len(person_ids) > MAX_BATCH_DELETE_COUNT:
        return jsonify({
            'error': f'单次最多删除 {MAX_BATCH_DELETE_COUNT} 条记录，当前选择了 {len(person_ids)} 条'
        }), 400
    
    # 要求确认（通过请求参数）
    confirm = data.get('confirm', False)
    if not confirm:
        return jsonify({
            'error': '需要确认',
            'require_confirm': True,
            'count': len(person_ids)
        }), 400
    
    session = get_session()
    try:
        # 支持人员ID和身份证号两种方式
        deleted_count = session.query(Person).filter(
            (Person.id.in_(person_ids)) | (Person.id_card.in_(person_ids))
        ).delete(synchronize_session='fetch')
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量删除人员",
            f"删除{deleted_count}人，ID列表: {','.join(person_ids[:10])}{'...' if len(person_ids) > 10 else ''}",
            request.remote_addr,
            "Web"
        )
        
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        session.rollback()
        return safe_exception(e, "删除失败", 500)
    finally:
        session.close()
