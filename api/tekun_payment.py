import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import func, distinct

from utils.security import require_auth
from utils.response import safe_error
from utils import escape_like
from database import get_session, TekunPayment, add_operation_log
from config import BASE_DIR

bp = Blueprint('tekun_payment', __name__)


@bp.route('/tekun_payment/import', methods=['POST'])
@require_auth
def import_tekun_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400

    tmp_path = os.path.join(BASE_DIR, f'_tmp_tekun_{secrets.token_hex(4)}.xlsx')

    try:
        file.save(tmp_path)
        from excel_importer import import_tekun_payment_excel
        period = request.form.get('period', '').strip()
        result = import_tekun_payment_excel(tmp_path, period=period)

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入特困数据",
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


@bp.route('/tekun_payment')
@require_auth
def list_tekun_payments():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')
    id_card = request.args.get('id_card', '')
    name = request.args.get('name', '')

    session = get_session()
    try:
        query = session.query(TekunPayment)

        if period:
            query = query.filter(TekunPayment.period == period)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(TekunPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if name:
            safe_name = escape_like(name)
            query = query.filter(TekunPayment.name.like(f'%{safe_name}%', escape='\\'))

        records = query.order_by(TekunPayment.period.desc()).limit(500).all()

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


@bp.route('/tekun_payment/years')
@require_auth
def get_tekun_payment_years():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        periods = session.query(distinct(TekunPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)
        return jsonify({'years': years})
    finally:
        session.close()


@bp.route('/tekun_payment/periods')
@require_auth
def get_tekun_payment_periods():
    session = get_session()
    try:
        periods = session.query(distinct(TekunPayment.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()


@bp.route('/tekun_payment/statistics')
@require_auth
def get_tekun_payment_statistics():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        periods = session.query(distinct(TekunPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)

        by_year = []
        total_amount = 0.0
        total_count = 0

        for year in years:
            records = session.query(TekunPayment).filter(
                TekunPayment.period.like(f'{year}%')
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


@bp.route('/tekun_payment/<record_id>', methods=['DELETE'])
@require_auth
def delete_tekun_payment(record_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        record = session.query(TekunPayment).filter(TekunPayment.id == record_id).first()
        if not record:
            return jsonify({'error': '记录不存在'}), 404

        session.delete(record)
        session.commit()

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除特困记录",
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


@bp.route('/tekun_payment/export')
@require_auth
def export_tekun_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')

    session = get_session()
    try:
        query = session.query(TekunPayment)
        if period:
            query = query.filter(TekunPayment.period == period)

        records = query.order_by(TekunPayment.period.desc()).all()

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
        tmp_path = os.path.join(BASE_DIR, f'_tmp_tekun_exp_{secrets.token_hex(4)}.xlsx')
        df.to_excel(tmp_path, index=False, engine='openpyxl')

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导出特困数据",
            f"导出{len(records)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return send_file(tmp_path, as_attachment=True,
                        download_name=f'特困数据_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
