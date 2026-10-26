from flask import jsonify

from database import get_session, EducationHistory
from utils.security import require_auth
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/education/history', methods=['GET'])
@require_auth
def api_get_education_history(person_id):
    """获取某人的就读历史记录（变更记录）。"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        rows = session.query(EducationHistory).filter(
            EducationHistory.person_id == p.id
        ).order_by(EducationHistory.change_date.desc()).all()
        return jsonify({
            'success': True,
            'history': [{
                'change_date': h.change_date,
                'school_name': h.school_name,
                'grade': h.grade,
                'class_name': h.class_name,
                'student_status': h.student_status,
                'change_reason': h.change_reason,
            } for h in rows]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
