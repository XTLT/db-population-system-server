import os
import secrets
from flask import request, jsonify

from utils.security import require_auth
from database import add_operation_log
from config import BASE_DIR
from . import bp


@bp.route('/elderly_allowance/import', methods=['POST'])
@require_auth
def import_elderly_allowance():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400

    tmp_path = os.path.join(BASE_DIR, f'_tmp_ea_{secrets.token_hex(4)}.xlsx')

    try:
        file.save(tmp_path)
        from excel_importer import import_elderly_allowance_excel
        period = request.form.get('period', '').strip()
        result = import_elderly_allowance_excel(tmp_path, period=period, import_source=file.filename)

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "高龄补贴",
            f"导入{result.get('imported', 0)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
