import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from utils.security import require_auth
from utils import escape_like
from database import get_session, TreatmentPayment, add_operation_log
from config import BASE_DIR

bp = Blueprint('treatment_payment', __name__)


@bp.route('/treatment_payment/import', methods=['POST'])
@require_auth
def import_treatment_payment():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '未选择文件'}), 400
    
    tmp_path = os.path.join(BASE_DIR, f'_tmp_treatment_{secrets.token_hex(4)}.xlsx')
    
    try:
        file.save(tmp_path)
        from excel_importer import import_treatment_payment_excel
        period = request.form.get('period', '').strip()
        result = import_treatment_payment_excel(tmp_path, period=period)
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导入医疗支付",
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


@bp.route('/treatment_payment')
@require_auth
def list_treatment_payments():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    period = request.args.get('period', '')
    id_card = request.args.get('id_card', '')
    name = request.args.get('name', '')
    subsidy_type = request.args.get('subsidy_type', '')
    
    session = get_session()
    try:
        query = session.query(TreatmentPayment)
        
        if period:
            query = query.filter(TreatmentPayment.period == period)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(TreatmentPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if name:
            safe_name = escape_like(name)
            query = query.filter(TreatmentPayment.name.like(f'%{safe_name}%', escape='\\'))
        if subsidy_type:
            query = query.filter(TreatmentPayment.subsidy_type == subsidy_type)
        
        payments = query.order_by(TreatmentPayment.period.desc()).limit(500).all()
        
        return jsonify({
            'payments': [{
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'town': p.town,
                'village': p.village,
                'period': p.period,
                'payment_status': p.payment_status,
                'bank_account': p.bank_account,
                'amount': p.amount,
                'subsidy_type': p.subsidy_type,
                'relation': p.relation,
                'fail_reason': p.fail_reason,
                'import_source': p.import_source,
                'import_time': p.import_time
            } for p in payments]
        })
    finally:
        session.close()


@bp.route('/treatment_payment/years')
@require_auth
def get_treatment_payment_years():
    """获取所有待遇发放年份"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        from sqlalchemy import distinct
        periods = session.query(distinct(TreatmentPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)
        return jsonify({'years': years})
    finally:
        session.close()


@bp.route('/treatment_payment/periods')
@require_auth
def get_treatment_payment_periods():
    """获取所有可用的费款所属期（按月）"""
    session = get_session()
    try:
        from sqlalchemy import distinct
        periods = session.query(distinct(TreatmentPayment.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()


@bp.route('/treatment_payment/statistics')
@require_auth
def get_treatment_payment_statistics():
    """获取待遇发放统计信息"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        from sqlalchemy import distinct
        periods = session.query(distinct(TreatmentPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)
        
        by_year = []
        total_amount = 0.0
        total_count = 0
        
        for year in years:
            payments = session.query(TreatmentPayment).filter(
                TreatmentPayment.period.like(f'{year}%')
            ).all()
            
            count = len(payments)
            amount = sum(float(p.amount or 0) for p in payments)
            
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


@bp.route('/treatment_payment/<payment_id>', methods=['DELETE'])
@require_auth
def delete_treatment_payment(payment_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        payment = session.query(TreatmentPayment).filter(TreatmentPayment.id == payment_id).first()
        if not payment:
            return jsonify({'error': '记录不存在'}), 404
        
        session.delete(payment)
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除医疗支付记录",
            payment_id,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()


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
        data = [{
            '所属乡镇': p.town,
            '所属村': p.village,
            '费款所属期': p.period,
            '姓名': p.name,
            '身份证号': p.id_card,
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
