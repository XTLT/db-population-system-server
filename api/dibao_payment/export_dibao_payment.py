import os
import secrets
from datetime import datetime
from flask import request, jsonify, send_file

from utils.security import require_auth
from utils.file_send import send_file_auto_cleanup, cleanup_temp
from database import get_session, DibaoPayment, add_operation_log
from config import BASE_DIR
from . import bp


@bp.route('/dibao_payment/export')
@require_auth
def export_dibao_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')

    session = get_session()
    try:
        query = session.query(DibaoPayment)
        if period:
            query = query.filter(DibaoPayment.period == period)

        records = query.order_by(DibaoPayment.period.desc()).all()

        if not records:
            return jsonify({'error': '没有数据可导出'}), 404

        import pandas as pd
        data = [{
            '村名称': p.village,
            '救助类型': '低保',
            '人员姓名': p.name,
            '人员身份证号': p.id_card,
            '性别': p.gender,
            '和申请人关系': p.relation,
            '共同生活家庭成员': p.family_members,
            '享受保障人口数': p.family_count,
            '家庭保障总金额': p.amount,
            '家庭最低生活基本保障金': p.base_amount,
            '家庭特殊困难补助金': p.special_amount,
            '家庭调剂金额': p.adjust_amount,
            '特殊困难情形（分类施保）': p.special_situation,
            '特殊困难补助金': p.special_subsidy,
            '初始享受时间': p.start_time,
            '始发年月': p.issue_month or p.period,
            '费款所属期': p.period,
            '导入来源': p.import_source,
            '导入时间': p.import_time
        } for p in records]

        df = pd.DataFrame(data)
        tmp_path = os.path.join(BASE_DIR, f'_tmp_dibao_exp_{secrets.token_hex(4)}.xlsx')
        df.to_excel(tmp_path, index=False, engine='openpyxl')

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导出低保数据",
            f"导出{len(records)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return send_file_auto_cleanup(tmp_path, as_attachment=True,
                        download_name=f'低保数据_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        if 'tmp_path' in locals():
            cleanup_temp(tmp_path)
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
