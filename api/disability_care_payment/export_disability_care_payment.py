import os
import secrets
from datetime import datetime
from flask import request, jsonify, send_file

from utils.security import require_auth
from utils.file_send import send_file_auto_cleanup, cleanup_temp
from database import get_session, DisabilityCarePayment, add_operation_log
from config import BASE_DIR
from . import bp


@bp.route('/disability_care_payment/export')
@require_auth
def export_disability_care_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')

    session = get_session()
    try:
        query = session.query(DisabilityCarePayment)
        if period:
            query = query.filter(DisabilityCarePayment.period == period)

        records = query.order_by(DisabilityCarePayment.period.desc()).all()

        if not records:
            return jsonify({'error': '没有数据可导出'}), 404

        import pandas as pd
        data = [{
            '所属乡镇': p.town,
            '所属村': p.village,
            '费款所属期': p.period,
            '姓名': p.name,
            '身份证号': p.id_card,
            '银行账号': p.bank_account,
            '金额': p.amount,
            '支付标志': p.payment_status,
            '和申请人关系': p.relation,
            '失败原因': p.fail_reason,
            '导入来源': p.import_source,
            '导入时间': p.import_time
        } for p in records]

        df = pd.DataFrame(data)
        tmp_path = os.path.join(BASE_DIR, f'_tmp_dcp_exp_{secrets.token_hex(4)}.xlsx')
        df.to_excel(tmp_path, index=False, engine='openpyxl')

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "残疾人护理补贴",
            f"导出{len(records)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return send_file_auto_cleanup(tmp_path, as_attachment=True,
                        download_name=f'残疾人护理补贴_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        if 'tmp_path' in locals():
            cleanup_temp(tmp_path)
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
