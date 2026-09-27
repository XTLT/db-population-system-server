from flask import request, jsonify

from utils.security import require_auth
from database import get_session, LandSubsidy, add_operation_log
from . import bp


@bp.route('/land_subsidy/<subsidy_id>', methods=['DELETE'])
@require_auth
def delete_subsidy(subsidy_id):
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        subsidy = session.query(LandSubsidy).filter(LandSubsidy.id == subsidy_id).first()
        if not subsidy:
            return jsonify({'error': '记录不存在'}), 404

        session.delete(subsidy)
        session.commit()

        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除补贴记录",
            subsidy_id,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )

        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
