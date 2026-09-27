import secrets
from flask import jsonify

from utils.security import require_auth
from . import bp


@bp.route('/students/template')
@require_auth
def download_student_template():
    import os
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
