"""POST /api/notifications/age-notice/handled：标记某位到龄人员已办理。"""

from flask import jsonify, request

from database import add_operation_log, mark_age_notice_handled
from utils.security import require_auth
from . import bp


@bp.route('/age-notice/handled', methods=['POST'])
@require_auth
def api_mark_age_notice_handled():
    data = request.get_json(silent=True) or {}
    person_id = (data.get('person_id') or '').strip()
    if not person_id:
        return jsonify({'success': False, 'message': '缺少 person_id'}), 400

    try:
        age_group = int(data.get('age_group', 60))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'age_group 必须是 60 或 80'}), 400
    if age_group not in (60, 80):
        return jsonify({'success': False, 'message': 'age_group 必须是 60 或 80'}), 400

    user = request.current_user
    mark_age_notice_handled(
        person_id,
        age_group=age_group,
        month=data.get('month', ''),
        operator=user.get('username', ''),
        person_name=data.get('name', ''),
        id_card=data.get('id_card', ''),
    )

    try:
        add_operation_log(
            user.get('id', ''),
            user.get('username', ''),
            '到龄提醒已办理',
            '%s (%d 周岁)' % (data.get('name', person_id), age_group),
        )
    except Exception:
        pass

    return jsonify({'success': True})
