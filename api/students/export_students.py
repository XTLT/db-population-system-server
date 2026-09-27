import secrets
from flask import request, jsonify

from utils.security import require_auth
from database import get_session, add_operation_log
from . import bp


@bp.route('/students/export', methods=['POST'])
@require_auth
def export_students():
    import os
    from flask import send_file
    from datetime import datetime
    from database import User
    
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json() or {}
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': '导出敏感数据需要验证密码'}), 401
    
    from utils.security import verify_password
    
    user_id = request.current_user['id']
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        is_valid, _ = verify_password(password, user.password_hash)
        if not is_valid:
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
