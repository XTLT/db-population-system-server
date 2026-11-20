"""POST /api/export/excel：导出人员数据到 Excel（需二次密码验证）。"""

import logging
import os
import secrets
from datetime import datetime

from flask import request, jsonify

from database import get_session, add_operation_log
from utils.security import get_client_ip, require_auth, verify_password
from utils.file_send import send_file_auto_cleanup, cleanup_temp
from config import BASE_DIR
from .friendly_error import friendly_error

logger = logging.getLogger(__name__)


@require_auth
def export_excel():
    from database import User
    from excel_importer import export_excel as do_export

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
        tmp_path = os.path.join(BASE_DIR, f'_tmp_export_{secrets.token_hex(4)}.xlsx')
        filters = data.get('filters') or {}

        if do_export(tmp_path, filters=filters):
            add_operation_log(
                request.current_user['id'],
                request.current_user['username'],
                "导出Excel",
                "导出人员数据",
                get_client_ip(),
                "Web"
            )
            return send_file_auto_cleanup(
                tmp_path, as_attachment=True,
                download_name=f'人口信息_{datetime.now().strftime("%Y%m%d")}.xlsx',
            )
        cleanup_temp(tmp_path)
        return jsonify({'error': '没有数据可导出'}), 404
    except Exception as e:
        if 'tmp_path' in locals():
            cleanup_temp(tmp_path)
        # 必须留完整堆栈：之前只返回 str(e)，用户报 IO_WRITE 时无从定位
        logger.exception('导出 Excel 失败 user=%s filters=%s',
                         request.current_user.get('username'),
                         data.get('filters'))
        return jsonify({'error': friendly_error(e)}), 400
