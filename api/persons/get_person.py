from flask import request, jsonify

from database import get_session, get_student_education, add_operation_log
from utils.security import require_auth
from config import GRADE_DISPLAY
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>')
@require_auth
def api_person(person_id):
    """获取人员详情"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error
        
        # 记录审计日志：查看敏感数据
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "查看人员详情",
            f"{p.name}({p.id_card[:6]}****{p.id_card[-4:]})" if p.id_card else p.name,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        edu = get_student_education(p.id)
        return jsonify({
            'person': {
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'hu_hao': p.hu_hao,
                'relation': p.relation,
                'address': p.address,
                'age': p.age,
                'phone': p.phone,
                'is_dead': p.is_dead,
                'social_card1': p.social_card1,
                'social_card2': p.social_card2,
                'social_card3': p.social_card3,
                'poor_type': p.poor_type,
                'remark': p.remark,
                'disability': p.disability,
                'disability_type': p.disability_type,
                'dis_level': p.dis_level,
                'dibao': p.dibao,
                'tekun': p.tekun or '',
                'tekun_type': p.tekun_type or '',
                'jisheng': p.jisheng,
                'is_migrated': p.is_migrated,
                'land_area': p.land_area or '',
                'land_area_change_reason': p.land_area_change_reason or '',
                'land_area_change_time': p.land_area_change_time or '',
                'local_welfare_forest_area': p.local_welfare_forest_area or '',
                'local_welfare_forest_change_reason': p.local_welfare_forest_change_reason or '',
                'local_welfare_forest_change_time': p.local_welfare_forest_change_time or '',
                'national_welfare_forest_area': p.national_welfare_forest_area or '',
                'national_welfare_forest_change_reason': p.national_welfare_forest_change_reason or '',
                'national_welfare_forest_change_time': p.national_welfare_forest_change_time or '',
                'commercial_forest_area': p.commercial_forest_area or '',
                'commercial_forest_change_reason': p.commercial_forest_change_reason or '',
                'commercial_forest_change_time': p.commercial_forest_change_time or '',
                'updated_at': p.updated_at or '',
                'education': {
                    'school_name': edu.school_name,
                    'grade': GRADE_DISPLAY.get(edu.grade, edu.grade) if edu.grade else '',
                    'class_name': edu.class_name,
                    'guardian': edu.guardian,
                    'guardian_phone': edu.guardian_phone,
                    'is_left_behind': edu.is_left_behind,
                    'student_status': edu.student_status,
                    'enrollment_date': edu.enrollment_date,
                    'graduation_date': edu.graduation_date
                } if edu else None
            }
        })
    finally:
        session.close()
