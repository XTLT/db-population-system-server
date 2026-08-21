import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import func

from utils.security import require_auth
from utils.response import safe_error
from utils import escape_like, validate_year
from database import get_session, TreatmentPayment, Person, add_operation_log
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
        result = import_treatment_payment_excel(tmp_path)
        
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
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    year = request.args.get('year', '')
    id_card = request.args.get('id_card', '')
    
    if year:
        valid, msg = validate_year(year)
        if not valid:
            return jsonify({'error': f'年份: {msg}'}), 400
    
    session = get_session()
    try:
        query = session.query(TreatmentPayment)
        
        if year:
            query = query.filter(TreatmentPayment.year == year)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(TreatmentPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        
        payments = query.order_by(TreatmentPayment.year.desc()).limit(500).all()
        
        return jsonify({
            'payments': [{
                'id': p.id,
                'person_id': p.person_id,
                'id_card': p.id_card,
                'name': p.name,
                'year': p.year,
                'amount': p.amount,
                'created_at': p.created_at
            } for p in payments]
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
    
    year = request.args.get('year', '')
    
    session = get_session()
    try:
        query = session.query(TreatmentPayment)
        if year:
            query = query.filter(TreatmentPayment.year == year)
        
        payments = query.order_by(TreatmentPayment.year.desc()).all()
        
        if not payments:
            return jsonify({'error': '没有数据可导出'}), 404
        
        import pandas as pd
        data = [{
            '身份证号': p.id_card,
            '姓名': p.name,
            '年份': p.year,
            '金额': p.amount,
            '创建时间': p.created_at
        } for p in payments]
        
        df = pd.DataFrame(data)
        tmp_path = os.path.join(BASE_DIR, f'_tmp_treatment_exp_{secrets.token_hex(4)}.xlsx')
        df.to_excel(tmp_path, index=False, engine='openpyxl')
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "导出医疗支付",
            f"导出{len(payments)}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return send_file(tmp_path, as_attachment=True,
                        download_name=f'医疗支付_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
