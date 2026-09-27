from flask import jsonify
from sqlalchemy import func

from database import get_session, StudentEducation
from utils.security import require_auth
from . import bp


@bp.route('/students/statistics')
@require_auth
def api_students_statistics():
    session = get_session()
    try:
        total = session.query(StudentEducation).count()
        
        studying = session.query(StudentEducation).filter(
            StudentEducation.student_status == '在读'
        ).count()
        
        graduated = session.query(StudentEducation).filter(
            StudentEducation.student_status == '离校'
        ).count()
        
        left_behind = session.query(StudentEducation).filter(
            StudentEducation.is_left_behind == '是'
        ).count()
        
        grade_stats = {}
        grades = session.query(StudentEducation.grade, func.count(StudentEducation.id)).group_by(
            StudentEducation.grade
        ).all()
        for grade, count in grades:
            if grade:
                grade_stats[grade] = count
        
        school_stats = {}
        schools = session.query(StudentEducation.school_name, func.count(StudentEducation.id)).group_by(
            StudentEducation.school_name
        ).all()
        for school, count in schools:
            if school:
                school_stats[school] = count

        status_stats = {}
        statuses = session.query(StudentEducation.student_status, func.count(StudentEducation.id)).group_by(
            StudentEducation.student_status
        ).all()
        for status, count in statuses:
            if status:
                status_stats[status] = count

        return jsonify({
            'total': total,
            'studying': studying,
            'graduated': graduated,
            'left_behind': left_behind,
            'grade_distribution': grade_stats,
            'school_distribution': school_stats,
            'status_distribution': status_stats
        })
    finally:
        session.close()
