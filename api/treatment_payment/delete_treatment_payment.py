from flask import request, jsonify

from utils.security import require_auth
from database import get_session, TreatmentPayment, add_operation_log
from . import bp


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
