from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from database import (
    get_session, Person, StudentEducation,
    get_person_count, search_students,
    get_person_trend_data, get_person_distribution, get_person_comparison
)
from utils.security import require_auth
from config import GRADE_DISPLAY


bp = Blueprint('statistics', __name__)


@bp.route('/statistics')
@require_auth
def api_statistics():
    session = get_session()
    try:
        total = session.query(Person).count()
        dead = session.query(Person).filter(Person.is_dead == '是').count()
        migrated = session.query(Person).filter(Person.is_migrated == '是').count()
        # 低保人员统计：匹配数据库中的实际值
        dibao = session.query(Person).filter(
            Person.dibao.in_(['最低生活保障家庭', '最低生活保障边缘家庭', '单人保家庭'])
        ).count()
        disability = session.query(Person).filter(Person.disability != '无', Person.disability != '').count()
        # 特困供养人员统计
        tekun = session.query(Person).filter(
            Person.tekun != '', Person.tekun != '否', Person.tekun.isnot(None)
        ).count()

        poor_type_distribution = {}
        poor_type_person_count = {}
        
        from sqlalchemy import case
        
        hu_hao_poor_types = session.query(
            Person.hu_hao,
            func.max(case((Person.relation == '户主', Person.poor_type), else_=None)).label('hu_zhu_type'),
            func.max(case((Person.poor_type != '', Person.poor_type), else_=None)).label('first_type')
        ).filter(
            Person.hu_hao != '', 
            Person.hu_hao.isnot(None)
        ).group_by(Person.hu_hao).all()
        
        for hu_hao, hu_zhu_type, first_type in hu_hao_poor_types:
            pt_val = hu_zhu_type or first_type or '其他'
            if pt_val:
                poor_type_distribution[pt_val] = poor_type_distribution.get(pt_val, 0) + 1

        # 统计各 poor_type 的人数
        pt_person_counts = session.query(
            Person.poor_type, func.count(Person.id)
        ).filter(
            Person.poor_type != '', Person.poor_type.isnot(None)
        ).group_by(Person.poor_type).all()
        for pt_val, cnt in pt_person_counts:
            poor_type_person_count[pt_val] = cnt

        dis_level_distribution = {}
        dis_levels = session.query(Person.dis_level).filter(
            Person.dis_level != '', Person.dis_level.isnot(None), Person.dis_level != '无'
        ).all()
        for dl in dis_levels:
            dl_val = dl[0] or '其他'
            dis_level_distribution[dl_val] = dis_level_distribution.get(dl_val, 0) + 1

        tekun_type_distribution = {}
        tekun_types = session.query(Person.tekun_type).filter(
            Person.tekun_type != '', Person.tekun_type.isnot(None)
        ).all()
        for tt in tekun_types:
            tt_val = tt[0] or '其他'
            tekun_type_distribution[tt_val] = tekun_type_distribution.get(tt_val, 0) + 1

        land_areas = session.query(Person.land_area).filter(
            Person.land_area != '', Person.land_area.isnot(None)
        ).all()
        total_land_area = 0.0
        land_count = 0
        for la in land_areas:
            try:
                area = float(la[0])
                total_land_area += area
                land_count += 1
            except (ValueError, TypeError):
                pass
        avg_land_area = round(total_land_area / land_count, 2) if land_count > 0 else 0

        return jsonify({
            'total': total,
            'dead': dead,
            'migrated': migrated,
            'dibao': dibao,
            'disability': disability,
            'tekun': tekun,
            'alive': total - dead,
            'not_migrated': total - migrated,
            'poor_type_distribution': poor_type_distribution,
            'poor_type_person_count': poor_type_person_count,
            'dis_level_distribution': dis_level_distribution,
            'tekun_type_distribution': tekun_type_distribution,
            'total_land_area': round(total_land_area, 2),
            'avg_land_area': avg_land_area
        })
    finally:
        session.close()


@bp.route('/stats')
@require_auth
def api_stats():
    return jsonify({
        'total_persons': get_person_count()
    })


@bp.route('/students')
@require_auth
def api_students():
    school = request.args.get('school')
    grade = request.args.get('grade')
    class_name = request.args.get('class_name')
    is_left_behind = request.args.get('is_left_behind')
    students = search_students(school, grade, class_name, is_left_behind)
    session = get_session()
    try:
        result = []
        for s in students:
            p = session.query(Person).filter(Person.id == s.person_id).first()
            result.append({
                'id': s.id,
                'person_id': s.person_id,
                'name': p.name if p else '',
                'id_card': s.id_card,
                'school_name': s.school_name,
                'grade': s.grade,
                'grade_display': GRADE_DISPLAY.get(s.grade, s.grade),
                'class_name': s.class_name,
                'guardian': s.guardian,
                'is_left_behind': s.is_left_behind,
                'student_status': s.student_status
            })
        return jsonify({'students': result})
    finally:
        session.close()


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
        
        return jsonify({
            'total': total,
            'studying': studying,
            'graduated': graduated,
            'left_behind': left_behind,
            'grade_distribution': grade_stats,
            'school_distribution': school_stats
        })
    finally:
        session.close()


@bp.route('/statistics/trend')
@require_auth
def api_statistics_trend():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    group_by = request.args.get('group_by', 'month')
    
    if group_by not in ['day', 'week', 'month', 'year']:
        group_by = 'month'
    
    if not start_date or not end_date:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')
    
    try:
        data = get_person_trend_data(start_date, end_date, group_by)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics/distribution')
@require_auth
def api_statistics_distribution():
    field = request.args.get('field', '')
    
    if not field:
        return jsonify({'error': '缺少field参数'}), 400
    
    valid_fields = ['disability', 'dibao', 'age_group', 'gender']
    if field not in valid_fields and not hasattr(Person, field):
        return jsonify({'error': f'无效的field参数，支持: {", ".join(valid_fields)}'}), 400
    
    try:
        data = get_person_distribution(field)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics/comparison')
@require_auth
def api_statistics_comparison():
    dimensions = request.args.getlist('dimensions')
    
    if not dimensions:
        dimensions = ['age', 'disability', 'dibao', 'migration', 'student']

    try:
        data = get_person_comparison(dimensions)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics/age_distribution')
@require_auth
def api_statistics_age_distribution():
    session = get_session()
    try:
        age_ranges = [
            ('0-18岁', 0, 18),
            ('19-30岁', 19, 30),
            ('31-40岁', 31, 40),
            ('41-50岁', 41, 50),
            ('51-60岁', 51, 60),
            ('60岁以上', 61, 200)
        ]
        
        all_ages = session.query(Person.age).filter(
            Person.age != '',
            Person.age.isnot(None)
        ).all()
        
        age_counts = {label: 0 for label, _, _ in age_ranges}
        
        for (age_str,) in all_ages:
            try:
                age = int(age_str)
                for label, min_age, max_age in age_ranges:
                    if min_age <= age <= max_age:
                        age_counts[label] += 1
                        break
            except (ValueError, TypeError):
                pass
        
        distribution = [
            {'range': label, 'count': age_counts[label]}
            for label, _, _ in age_ranges
        ]
        
        return jsonify({'distribution': distribution})
    finally:
        session.close()


@bp.route('/statistics/by_village')
@require_auth
def api_statistics_by_village():
    session = get_session()
    try:
        villages = session.query(Person.address, func.count(Person.id)).group_by(
            Person.address
        ).all()
        
        village_stats = []
        for address, count in villages:
            if address:
                village_stats.append({
                    'village': address,
                    'count': count
                })
        
        return jsonify({'villages': village_stats[:50]})
    finally:
        session.close()
