from flask import jsonify

from database import get_session, EducationHistory
from utils.security import require_auth
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/education/history/<history_id>', methods=['DELETE'])
@require_auth
def api_delete_education_history(person_id, history_id):
    """删除一条就读历史记录（误修改后允许删除错误记录）。"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        h = session.query(EducationHistory).filter(
            EducationHistory.id == history_id,
            EducationHistory.person_id == p.id
        ).first()
        if not h:
            return jsonify({'error': '记录不存在'}), 404
        session.delete(h)
        session.commit()
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
