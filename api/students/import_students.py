import secrets
from flask import request, jsonify

from utils.security import require_auth
from database import add_operation_log
from . import bp


@bp.route('/students/import', methods=['POST'])
@require_auth
def import_students():
    import os
    
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
