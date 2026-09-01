import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func

from utils.security import require_auth
from utils.response import get_json_data, safe_error
from utils import validate_id_card, validate_phone
from database import get_session, Person, StudentEducation, add_operation_log
from config import GRADE_DISPLAY

bp = Blueprint('students', __name__)


@bp.route('/student/<id_card>')
@require_auth
def get_student(id_card):
    session = get_session()
    try:
        student = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        person = session.query(Person).filter(Person.id == student.person_id).first()
        
        return jsonify({
            'student': {
                'id': student.id,
                'person_id': student.person_id,
                'id_card': student.id_card,
                'name': person.name if person else '',
                'school_name': student.school_name,
                'grade': student.grade,
                'grade_display': GRADE_DISPLAY.get(student.grade, student.grade),
                'class_name': student.class_name,
                'guardian': student.guardian,
                'guardian_phone': student.guardian_phone,
                'is_left_behind': student.is_left_behind,
                'student_status': student.student_status,
                'enrollment_date': student.enrollment_date,
                'graduation_date': student.graduation_date
            }
        })
    finally:
        session.close()


@bp.route('/student', methods=['POST'])
@require_auth
def create_student():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data, err = get_json_data()
    if err:
        return err
    
    id_card = data.get('id_card', '')
    if not id_card:
        return jsonify({'error': '身份证号不能为空'}), 400
    
    valid, msg = validate_id_card(id_card)
    if not valid:
        return jsonify({'error': msg}), 400
    
    guardian_phone = data.get('guardian_phone', '')
    if guardian_phone:
        valid, msg = validate_phone(guardian_phone)
        if not valid:
            return jsonify({'error': f'监护人电话: {msg}'}), 400
    
    session = get_session()
    try:
        existing = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        if existing:
            return jsonify({'error': '该身份证号的学生已存在'}), 400
        
        person = session.query(Person).filter(Person.id_card == id_card).first()
        person_id = person.id if person else ''
        
        student = StudentEducation(
            id=f"edu_{secrets.token_hex(8)}",
            person_id=person_id,
            id_card=id_card,
            school_name=data.get('school_name', ''),
            grade=data.get('grade', ''),
            class_name=data.get('class_name', ''),
            guardian=data.get('guardian', ''),
            guardian_phone=data.get('guardian_phone', ''),
            is_left_behind=data.get('is_left_behind', '否'),
            student_status=data.get('student_status', ''),
            enrollment_date=data.get('enrollment_date', '')
        )
        
        session.add(student)
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "添加学生",
            id_card,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Mobile')
        )
        
        return jsonify({'success': True, 'id': student.id})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()


@bp.route('/student/<id_card>', methods=['PUT'])
@require_auth
def update_student(id_card):
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data, err = get_json_data()
    if err:
        return err
    
    session = get_session()
    try:
        student = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        updatable_fields = [
            'school_name', 'grade', 'class_name', 
            'guardian', 'guardian_phone', 
            'is_left_behind', 'student_status', 'enrollment_date'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(student, field, data[field])
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "更新学生信息",
            id_card,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Mobile')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()


@bp.route('/student/<id_card>', methods=['DELETE'])
@require_auth
def delete_student(id_card):
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        student = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        session.delete(student)
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除学生",
            id_card,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Mobile')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()


@bp.route('/students/search')
@require_auth
def search_students_api():
    name = request.args.get('name')
    school = request.args.get('school')
    grade = request.args.get('grade')
    class_name = request.args.get('class_name')
    is_left_behind = request.args.get('is_left_behind')

    session = get_session()
    try:
        query = session.query(StudentEducation).join(
            Person, StudentEducation.person_id == Person.id
        )

        if name and name.strip():
            safe_name = name.strip().replace('%', '\\%').replace('_', '\\_')
            query = query.filter(Person.name.like(f'%{safe_name}%', escape='\\'))

        if school and school.strip():
            safe_school = school.strip().replace('%', '\\%').replace('_', '\\_')
            query = query.filter(StudentEducation.school_name.like(f'%{safe_school}%', escape='\\'))

        if grade and grade.strip():
            query = query.filter(StudentEducation.grade == grade.strip())

        if class_name and class_name.strip():
            safe_class = class_name.strip().replace('%', '\\%').replace('_', '\\_')
            query = query.filter(StudentEducation.class_name.like(f'%{safe_class}%', escape='\\'))

        if is_left_behind and is_left_behind.strip():
            query = query.filter(StudentEducation.is_left_behind == is_left_behind.strip())

        students = query.limit(100).all()

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
                'guardian_phone': s.guardian_phone,
                'is_left_behind': s.is_left_behind,
                'student_status': s.student_status,
                'enrollment_date': s.enrollment_date,
                'graduation_date': s.graduation_date
            })
        return jsonify({'results': result})
    finally:
        session.close()


@bp.route('/students/batch-delete', methods=['POST'])
@require_auth
def batch_delete_students():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    student_ids = data.get('ids', [])
    
    if not student_ids:
        return jsonify({'error': '未选择学生'}), 400
    
    if len(student_ids) > 100:
        return jsonify({
            'error': f'单次最多删除 100 条记录，当前选择了 {len(student_ids)} 条'
        }), 400
    
    confirm = data.get('confirm', False)
    if not confirm:
        return jsonify({
            'error': '需要确认',
            'require_confirm': True,
            'count': len(student_ids)
        }), 400
    
    session = get_session()
    try:
        deleted_count = session.query(StudentEducation).filter(
            StudentEducation.id.in_(student_ids)
        ).delete(synchronize_session='fetch')
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量删除学生",
            f"删除{deleted_count}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()


STUDENT_BATCH_UPDATE_ALLOWED_FIELDS = {
    'school_name', 'grade', 'class_name', 'guardian', 
    'guardian_phone', 'is_left_behind', 'student_status'
}


@bp.route('/students/batch-update', methods=['POST'])
@require_auth
def batch_update_students():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    student_ids = data.get('ids', [])
    updates = data.get('updates', {})
    
    if not student_ids:
        return jsonify({'error': '未选择学生'}), 400
    
    if not updates:
        return jsonify({'error': '未提供更新内容'}), 400
    
    if len(student_ids) > 200:
        return jsonify({
            'error': f'单次最多更新 200 条记录，当前选择了 {len(student_ids)} 条'
        }), 400
    
    filtered_updates = {
        k: v for k, v in updates.items() 
        if k in STUDENT_BATCH_UPDATE_ALLOWED_FIELDS
    }
    
    if not filtered_updates:
        return jsonify({'error': '没有有效的更新字段'}), 400
    
    session = get_session()
    try:
        students = session.query(StudentEducation).filter(
            StudentEducation.id.in_(student_ids)
        ).all()
        updated_count = 0
        
        for student in students:
            for key, value in filtered_updates.items():
                setattr(student, key, value)
            updated_count += 1
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量更新学生",
            f"更新{updated_count}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify({'success': True, 'updated': updated_count})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()


@bp.route('/students/import', methods=['POST'])
@require_auth
def import_students():
    import os
    import secrets
    
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400
    
    from config import BASE_DIR
    tmp_path = os.path.join(BASE_DIR, f'_tmp_stu_{secrets.token_hex(4)}.xlsx')
    
    try:
        file.save(tmp_path)
        from student_importer import import_student_education
        result = import_student_education(tmp_path)
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入学生数据",
            f"导入{result.get('imported', 0)}条，更新{result.get('updated', 0)}条",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@bp.route('/students/export', methods=['POST'])
@require_auth
def export_students():
    import os
    import secrets
    import hashlib
    from flask import send_file
    from datetime import datetime
    from database import User
    
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json() or {}
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': '导出敏感数据需要验证密码'}), 401
    
    user_id = request.current_user['id']
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        salt, stored_hash = user.password_hash.split(":")
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        if password_hash != stored_hash:
            return jsonify({'error': '密码错误'}), 401
    finally:
        session.close()
    
    from config import BASE_DIR
    from student_importer import export_student_education
    
    tmp_path = os.path.join(BASE_DIR, f'_tmp_stu_exp_{secrets.token_hex(4)}.xlsx')
    try:
        if export_student_education(tmp_path):
            add_operation_log(
                request.current_user['id'],
                request.current_user['username'],
                "导出敏感数据",
                "导出学生就读信息Excel",
                request.remote_addr,
                request.headers.get('X-Client-Type', 'Web')
            )
            return send_file(tmp_path, as_attachment=True, 
                           download_name=f'学生就读信息_{datetime.now().strftime("%Y%m%d")}.xlsx')
        return jsonify({'error': '没有数据可导出'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/students/promote', methods=['POST'])
@require_auth
def promote_grades():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    from database import promote_all_grades
    try:
        count = promote_all_grades()
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "年级升级",
            f"升级{count}名学生",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/students/template')
@require_auth
def download_student_template():
    import os
    import secrets
    from flask import send_file
    from config import BASE_DIR
    
    tmp_path = os.path.join(BASE_DIR, f'_tmp_stu_tpl_{secrets.token_hex(4)}.xlsx')
    try:
        from student_importer import export_student_education_template
        export_student_education_template(tmp_path)
        return send_file(tmp_path, as_attachment=True, 
                        download_name='学生就读信息导入模板.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
