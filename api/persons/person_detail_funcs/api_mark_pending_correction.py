"""POST /api/persons/pending-correction/handled：把待核销清单里的人标记为已核销。

标记后该人不再出现在待核销清单；名下补贴记录本身不动（仍需到对应模块处理）。
"""

from flask import jsonify, request

from database import add_operation_log, mark_pending_correction_handled
from utils.security import get_client_ip, require_auth


@require_auth
def api_mark_pending_correction_handled():
    data = request.get_json(silent=True) or {}
    person_id = (data.get('person_id') or '').strip()
    if not person_id:
        return jsonify({'error': '缺少 person_id'}), 400

    name = (data.get('name') or '').strip()
    id_card = (data.get('id_card') or '').strip()
    labels = (data.get('module_labels') or '').strip()
    try:
        module_count = int(data.get('module_count') or 0)
    except (TypeError, ValueError):
        module_count = 0
    total_amount = (data.get('total_amount') or '').strip()

    user = request.current_user
    try:
        mark_pending_correction_handled(
            person_id,
            operator=user.get('username', ''),
            person_name=name,
            id_card=id_card,
            module_labels=labels,
            module_count=module_count,
            total_amount=total_amount,
        )
        add_operation_log(
            user['id'],
            user['username'],
            '待核销已核销',
            '%s %s' % (name or person_id, id_card),
            get_client_ip(),
            request.headers.get('X-Client-Type', 'Web'),
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
