from utils.security import get_client_ip
import logging
import os
import secrets
from datetime import datetime
from flask import request, jsonify, send_file

from database import get_session, add_operation_log
from utils.security import require_auth
from utils.file_send import send_file_auto_cleanup, cleanup_temp
from config import BASE_DIR
from . import bp

logger = logging.getLogger(__name__)


def _friendly_error(exc):
    """把底层异常翻译成用户能看懂的话。

    原始实现直接 str(e) 返回，磁盘满/权限不足/TLS 中断这类底层错误会
    原样吐成 "IO_WRITE"、"[Errno 28] ..." 之类，用户完全无从判断。
    """
    msg = str(exc or '').strip()
    low = msg.lower()
    if 'no space left' in low or 'errno 28' in low or 'disk full' in low:
        return '服务器存储空间不足，导出失败，请联系管理员清理后重试'
    if 'permission denied' in low or 'errno 13' in low:
        return '服务器无权限写入导出文件，请联系管理员'
    if 'io_write' in low or 'io_read' in low or 'sslerror' in low or 'ssl' in low:
        return '导出过程中连接中断，请重试'
    if 'errno 122' in low or 'disk quota' in low:
        return '服务器存储配额不足，导出失败，请联系管理员'
    if msg and len(msg) <= 120:
        return '导出失败：%s' % msg
    return '导出失败，请重试或联系管理员'


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
                get_client_ip(),
                "Web"
            )
            return send_file_auto_cleanup(tmp_path, as_attachment=True,
                                          download_name=f'人口信息_{datetime.now().strftime("%Y%m%d")}.xlsx')
        cleanup_temp(tmp_path)
        return jsonify({'error': '没有数据可导出'}), 404
    except Exception as e:
        if 'tmp_path' in locals():
            cleanup_temp(tmp_path)
        # 必须留完整堆栈：之前只返回 str(e)，用户报 IO_WRITE 时无从定位
        logger.exception('导出 Excel 失败 user=%s filters=%s',
                         request.current_user.get('username'),
                         data.get('filters'))
        return jsonify({'error': _friendly_error(e)}), 400
