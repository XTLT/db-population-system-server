from flask import request, jsonify

from database import get_session, StudentEducation, add_operation_log
from utils.security import require_auth
from utils.response import get_json_data
from config import GRADE_CODE_MAP
from . import bp
from ._helpers import safe_id_card_query


@bp.route('/person/<person_id>/education', methods=['PUT'])
@require_auth
def api_save_education(person_id):
    """保存就读信息"""
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    data, err = get_json_data()
    if err:
        return err
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        from database import delete_student_education
        edu = session.query(StudentEducation).filter(StudentEducation.person_id == p.id).first()

        school = data.get('school_name', '').strip()
        grade = data.get('grade', '')
        class_name = data.get('class_name', '').strip()

        # 将中文年级名称转换为代码（如果需要）
        if grade and grade in GRADE_CODE_MAP:
            grade = GRADE_CODE_MAP[grade]

        if not school and not grade and not class_name:
            if edu:
                delete_student_education(p.id)
            return jsonify({'success': True})

        if edu:
            # 记录就读变更历史（与本地 save_student_education 行为一致）：
            # 学校/年级/班级/学生状态任一变化时，把修改前的值存入 education_history
            new_status = data.get('student_status', '')
            changed = (
                edu.school_name != school or
                edu.grade != grade or
                edu.class_name != class_name or
                edu.student_status != new_status
            )
            if changed:
                from datetime import datetime
                import uuid
                from database.models.education_history import EducationHistory
                history = EducationHistory(
                    id=str(uuid.uuid4()),
                    person_id=p.id,
                    id_card=p.id_card,
                    school_name=edu.school_name,
                    grade=edu.grade,
                    class_name=edu.class_name,
                    student_status=edu.student_status,
                    change_date=datetime.now().strftime("%Y-%m-%d"),
                    change_reason="编辑更新"
                )
                session.add(history)
            edu.school_name = school
            edu.grade = grade
            edu.class_name = class_name
            edu.guardian = data.get('guardian', '')
            edu.guardian_phone = data.get('guardian_phone', '')
            edu.is_left_behind = data.get('is_left_behind', '否')
            edu.student_status = new_status
            edu.enrollment_date = data.get('enrollment_date', '')
            edu.graduation_date = data.get('graduation_date', '')
        else:
            edu = StudentEducation(
                id=f"edu_{p.id}",
                person_id=p.id,
                id_card=p.id_card,
                school_name=school,
                grade=grade,
                class_name=class_name,
                guardian=data.get('guardian', ''),
                guardian_phone=data.get('guardian_phone', ''),
                is_left_behind=data.get('is_left_behind', '否'),
                student_status=data.get('student_status', ''),
                enrollment_date=data.get('enrollment_date', ''),
                graduation_date=data.get('graduation_date', '')
            )
            session.add(edu)
        session.commit()
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "修改就读信息",
            p.name,
            request.remote_addr,
            "Web"
        )
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
