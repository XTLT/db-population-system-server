from utils.security import get_client_ip
import os
import secrets
from flask import request, jsonify

from utils.security import require_auth
from utils import validate_year
from database import add_operation_log
from config import BASE_DIR
from . import bp


@bp.route('/land_subsidy/import', methods=['POST'])
@require_auth
def import_land_subsidy():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    subsidy_year = request.form.get('subsidy_year', '')

    if subsidy_year:
        valid, msg = validate_year(subsidy_year)
        if not valid:
            return jsonify({'error': f'补贴年份: {msg}'}), 400

    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400

    tmp_path = os.path.join(BASE_DIR, f'_tmp_land_{secrets.token_hex(4)}.xlsx')

    try:
        file.save(tmp_path)
        from excel_importer import import_land_subsidy_excel
        dry_run = request.form.get('dry_run', '').strip().lower() in ('1', 'true', 'yes')
        result = import_land_subsidy_excel(tmp_path, subsidy_year, dry_run=dry_run)

        if dry_run:
            return jsonify(result)

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入土地补贴",
            f"导入{result.get('imported', 0)}条记录",
            get_client_ip(),
            request.headers.get('X-Client-Type', 'Web')
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
