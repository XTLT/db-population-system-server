"""GET /api/person/<person_id>：人员详情。"""

from flask import request, jsonify

from database import get_session, get_student_education, add_operation_log
from utils.security import get_client_ip, require_auth
from .._helpers import safe_id_card_query
from .build_person_detail import build_person_detail


@require_auth
def api_person(person_id):
    """获取人员详情"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        # 记录审计日志：查看敏感数据
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "查看人员详情",
            f"{p.name}({p.id_card[:6]}****{p.id_card[-4:]})" if p.id_card else p.name,
            get_client_ip(),
            request.headers.get('X-Client-Type', 'Web'),
        )

        edu = get_student_education(p.id)
        return jsonify({'person': build_person_detail(p, edu)})
    finally:
        session.close()
