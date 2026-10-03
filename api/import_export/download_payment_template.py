import os
import secrets
from flask import jsonify, send_file

from utils.security import require_auth
from config import BASE_DIR
from . import bp
from ._constants import PAYMENT_TEMPLATE_MAP


@bp.route('/template/payment/<payment_type>')
@require_auth
def download_payment_template(payment_type):
    """下载支付类导入模板

    Args:
        payment_type: land_subsidy | pension_insurance | dibao_payment | tekun_payment

    Returns:
        Excel 模板文件
    """
    config = PAYMENT_TEMPLATE_MAP.get(payment_type)
    if not config:
        return jsonify({'error': f'未知的模板类型: {payment_type}'}), 400

    module_name, func_name, download_name = config
    tmp_path = os.path.join(BASE_DIR, f'_tmp_tpl_{payment_type}_{secrets.token_hex(4)}.xlsx')

    try:
        import importlib
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        func(tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
