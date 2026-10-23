import os
import secrets
from flask import jsonify, send_file

from utils.security import require_auth
from utils.file_send import send_file_auto_cleanup, cleanup_temp
from config import BASE_DIR
from . import bp


@bp.route('/template/forest')
@require_auth
def download_forest_template():
    """下载林地面积导入模板

    Returns:
        Excel 模板文件
    """
    tmp_path = os.path.join(BASE_DIR, f'_tmp_forest_tpl_{secrets.token_hex(4)}.xlsx')

    try:
        from excel_forest_template import generate_forest_template
        generate_forest_template(tmp_path)
        return send_file_auto_cleanup(tmp_path, as_attachment=True,
                        download_name='林地面积导入模板.xlsx')
    except Exception as e:
        if 'tmp_path' in locals():
            cleanup_temp(tmp_path)
        return jsonify({'error': str(e)}), 400
