import os
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename

from database import create_report_file, add_report_log
from utils.security import require_auth
from config import REPORTS_DIR
from . import bp
from ._allowed_file import _allowed_file


@bp.route('/upload', methods=['POST'])
@require_auth
def api_upload_report():
    """上传 Excel 报表文件"""
    user = request.current_user

    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400

    original_name = file.filename
    if not _allowed_file(original_name):
        return jsonify({'error': '仅支持 .xlsx .xls .et 格式'}), 400

    name = request.form.get('name', '').strip()
    if not name:
        name = original_name

    file_data = file.read()
    file_size = len(file_data)

    stored_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(original_name)}"
    file_path = os.path.join(REPORTS_DIR, stored_filename)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(file_data)

    report = create_report_file(
        name=name,
        original_name=original_name,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=file_size,
        user_id=user['id'],
        username=user['username'],
    )

    add_report_log(
        report_id=report['report_id'],
        user_id=user['id'],
        username=user['username'],
        operation_type='上传报表',
        operation_detail=f'文件:{original_name}, 名称:{name}',
        ip_address=request.remote_addr,
        client_type='Desktop',
    )

    return jsonify({'success': True, 'report': report})
