from flask import request, jsonify

from utils.security import require_auth
from database import get_session, DisabilityCarePayment, add_operation_log
from . import bp


@bp.route('/disability_care_payment/<record_id>', methods=['DELETE'])
@require_auth
def delete_disability_care_payment(record_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        record = session.query(DisabilityCarePayment).filter(DisabilityCarePayment.id == record_id).first()
        if not record:
            return jsonify({'error': '记录不存在'}), 404

        session.delete(record)
        session.commit()

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "残疾人护理补贴",
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
