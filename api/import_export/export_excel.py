import os
import secrets
from datetime import datetime
from flask import request, jsonify, send_file

from database import get_session, add_operation_log
from utils.security import require_auth
from config import BASE_DIR
from . import bp


@bp.route('/export/excel', methods=['POST'])
@require_auth
def export_excel():
    """导出人员数据到 Excel
    
    权限要求: admin 或 user
    需要二次密码验证
    
    Request Body:
        password: 用户密码
        filters: 筛选条件（可选）
    """
    from database import User
    from utils.security import verify_password
    
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
        
        is_valid, _ = verify_password(password, user.password_hash)
        if not is_valid:
            return jsonify({'error': '密码错误'}), 401
    finally:
        session.close()
    
    try:
        from excel_importer import export_excel as do_export
        tmp_path = os.path.join(BASE_DIR, f'_tmp_export_{secrets.token_hex(4)}.xlsx')
        filters = data.get('filters') or {}
        
        if do_export(tmp_path, filters=filters):
            add_operation_log(
                request.current_user['id'],
                request.current_user['username'],
                "导出Excel",
                "导出人员数据",
                request.remote_addr,
                "Web"
            )
            return send_file(tmp_path, as_attachment=True,
                           download_name=f'人口信息_{datetime.now().strftime("%Y%m%d")}.xlsx')
        return jsonify({'error': '没有数据可导出'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
