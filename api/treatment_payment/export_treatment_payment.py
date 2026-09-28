import os
import secrets
from datetime import datetime
from flask import request, jsonify, send_file

from utils.security import require_auth
from database import get_session, Person, TreatmentPayment, add_operation_log
from config import BASE_DIR
from . import bp


@bp.route('/treatment_payment/export')
@require_auth
def export_treatment_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')
    subsidy_type = request.args.get('subsidy_type', '')

    session = get_session()
    try:
        query = session.query(TreatmentPayment)
        if period:
            query = query.filter(TreatmentPayment.period == period)
        if subsidy_type:
            query = query.filter(TreatmentPayment.subsidy_type == subsidy_type)

        payments = query.order_by(TreatmentPayment.period.desc()).all()

        if not payments:
            return jsonify({'error': '没有数据可导出'}), 404

        import pandas as pd
        person_map = {p.id_card: p.dis_level for p in session.query(Person).all()}
        data = [{
            '所属乡镇': p.town,
            '所属村': p.village,
            '费款所属期': p.period,
            '姓名': p.name,
            '身份证号': p.id_card,
            '残疾等级': person_map.get(p.id_card, ''),
            '银行账号': p.bank_account,
            '金额': p.amount,
            '支付标志': p.payment_status,
            '救助类型': p.subsidy_type,
            '和申请人关系': p.relation,
            '失败原因': p.fail_reason,
            '导入来源': p.import_source,
            '导入时间': p.import_time
        } for p in payments]

        df = pd.DataFrame(data)
        tmp_path = os.path.join(BASE_DIR, f'_tmp_treatment_exp_{secrets.token_hex(4)}.xlsx')
        df.to_excel(tmp_path, index=False, engine='openpyxl')

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导出待遇发放",
            f"导出{len(payments)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return send_file(tmp_path, as_attachment=True,
                        download_name=f'待遇发放_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
