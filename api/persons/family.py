from datetime import datetime
from flask import request, jsonify

from database import get_family_members, get_student_education
from utils.security import require_auth
from config import GRADE_DISPLAY
from excel_importer import get_person_subsidy_total
from . import bp


@bp.route('/family/<hu_hao>')
@require_auth
def api_family(hu_hao):
    """获取家庭成员"""
    members = get_family_members(hu_hao)
    current_year = str(datetime.now().year)
    result = []
    for m in members:
        edu = get_student_education(m.id)
        student_mark = ""
        if edu:
            grade_display = GRADE_DISPLAY.get(edu.grade, edu.grade)
            student_mark = f"{grade_display} {edu.school_name}"
        subsidy_amount = get_person_subsidy_total(m.id_card, current_year)
        result.append({
            'id': m.id,
            'name': m.name,
            'id_card': m.id_card,
            'relation': m.relation,
            'address': m.address,
            'group_name': m.group_name or '',
            'age': m.age,
            'phone': m.phone,
            'is_dead': m.is_dead,
            'social_card1': m.social_card1,
            'social_card2': m.social_card2,
            'social_card3': m.social_card3,
            'social_card2_source': m.social_card2_source or '',
            'social_card3_source': m.social_card3_source or '',
            'poor_type': m.poor_type,
            'remark': m.remark,
            'disability': m.disability,
            'disability_type': m.disability_type or '',
            'dis_level': m.dis_level,
            'dibao': m.dibao,
            'tekun': m.tekun or '',
            'tekun_type': m.tekun_type or '',
            'jisheng': m.jisheng,
            'is_migrated': m.is_migrated,
            'land_area': m.land_area or '',
            'land_area_change_reason': m.land_area_change_reason or '',
            'land_area_change_time': m.land_area_change_time or '',
            'local_welfare_forest_area': m.local_welfare_forest_area or '',
            'local_welfare_forest_change_reason': m.local_welfare_forest_change_reason or '',
            'local_welfare_forest_change_time': m.local_welfare_forest_change_time or '',
            'national_welfare_forest_area': m.national_welfare_forest_area or '',
            'national_welfare_forest_change_reason': m.national_welfare_forest_change_reason or '',
            'national_welfare_forest_change_time': m.national_welfare_forest_change_time or '',
            'commercial_forest_area': m.commercial_forest_area or '',
            'commercial_forest_change_reason': m.commercial_forest_change_reason or '',
            'commercial_forest_change_time': m.commercial_forest_change_time or '',
            'student_mark': student_mark,
            'subsidy_amount': subsidy_amount
        })
    return jsonify({'members': result})
