import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import func, distinct

from utils.security import require_auth
from utils.response import safe_error
from utils import escape_like
from database import get_session, DibaoPayment, add_operation_log
from config import BASE_DIR

bp = Blueprint('dibao_payment', __name__)


@bp.route('/dibao_payment/import', methods=['POST'])
@require_auth
def import_dibao_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400

    tmp_path = os.path.join(BASE_DIR, f'_tmp_dibao_{secrets.token_hex(4)}.xlsx')

    try:
        file.save(tmp_path)
        from excel_importer import import_dibao_payment_excel
        result = import_dibao_payment_excel(tmp_path)

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入低保数据",
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


@bp.route('/dibao_payment')
@require_auth
def list_dibao_payments():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')
    id_card = request.args.get('id_card', '')
    name = request.args.get('name', '')

    session = get_session()
    try:
        query = session.query(DibaoPayment)

        if period:
            query = query.filter(DibaoPayment.period == period)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(DibaoPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if name:
            safe_name = escape_like(name)
            query = query.filter(DibaoPayment.name.like(f'%{safe_name}%', escape='\\'))

        records = query.order_by(DibaoPayment.period.desc()).limit(500).all()

        return jsonify({
            'records': [{
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'town': p.town,
                'village': p.village,
                'period': p.period,
                'payment_status': p.payment_status,
                'personal_code': p.personal_code,
                'bank_account': p.bank_account,
                'amount': p.amount,
                'relation': p.relation,
                'fail_reason': p.fail_reason,
                'import_source': p.import_source,
                'import_time': p.import_time
            } for p in records]
        })
    finally:
        session.close()


@bp.route('/dibao_payment/years')
@require_auth
def get_dibao_payment_years():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        periods = session.query(distinct(DibaoPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)
        return jsonify({'years': years})
    finally:
        session.close()


@bp.route('/dibao_payment/periods')
@require_auth
def get_dibao_payment_periods():
    session = get_session()
    try:
        periods = session.query(distinct(DibaoPayment.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()


@bp.route('/dibao_payment/statistics')
@require_auth
def get_dibao_payment_statistics():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        periods = session.query(distinct(DibaoPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)

        by_year = []
        total_amount = 0.0
        total_count = 0

        for year in years:
            records = session.query(DibaoPayment).filter(
                DibaoPayment.period.like(f'{year}%')
            ).all()

            count = len(records)
            amount = sum(float(p.amount or 0) for p in records)

            by_year.append({
                'year': year,
                'count': count,
                'amount': amount
            })

            total_count += count
            total_amount += amount

        return jsonify({
            'by_year': by_year,
            'total_amount': total_amount,
            'total_count': total_count
        })
    finally:
        session.close()


@bp.route('/dibao_payment/<record_id>', methods=['DELETE'])
@require_auth
def delete_dibao_payment(record_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        record = session.query(DibaoPayment).filter(DibaoPayment.id == record_id).first()
        if not record:
            return jsonify({'error': '记录不存在'}), 404

        session.delete(record)
        session.commit()

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除低保记录",
            record_id,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()


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

        return send_file(tmp_path, as_attachment=True,
                        download_name=f'低保数据_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
