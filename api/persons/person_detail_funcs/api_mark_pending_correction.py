"""POST /api/persons/pending-correction/handled：把待核销清单里的人标记为已核销。

核销后该人不再出现在待核销清单；名下补贴记录本身不动（仍需到对应模块处理）。
核销时的补贴快照（模块 / 笔数 / 合计金额）由服务端按当前数据现算并存下，
之后补发/新增了补贴（快照签名变化）该人会重新回到清单。
"""

from flask import jsonify, request

from database import add_operation_log, get_session, mark_pending_correction_handled
from utils.security import get_client_ip, require_auth
from .subsidy_snapshot import signature_for_person
from .to_amount import to_amount


@require_auth
def api_mark_pending_correction_handled():
    data = request.get_json(silent=True) or {}
    person_id = (data.get('person_id') or '').strip()
    if not person_id:
        return jsonify({'error': '缺少 person_id'}), 400

    name = (data.get('name') or '').strip()
    id_card = (data.get('id_card') or '').strip()

    # 快照以服务端现算的为准，不信任客户端传来的
    session = get_session()
    try:
        snapshot, module_list = signature_for_person(session, id_card)
    finally:
        session.close()
    labels = '、'.join([m['label'] for m in module_list])
    module_count = len(module_list)
    amount_sum = sum(to_amount(m.get('total_amount') or '') for m in module_list)
    total_amount = f"{amount_sum:.2f}" if amount_sum else ''

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
            snapshot=snapshot,
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
