"""GET /api/notifications/age-notice：到龄待办名单（累积，逐人可标记已办理）。"""

import logging

from flask import jsonify, request

from database import ensure_age_notifications, list_age_notice
from utils.security import require_auth
from . import bp

logger = logging.getLogger(__name__)


@bp.route('/age-notice', methods=['GET'])
@require_auth
def api_age_notice():
    age = request.args.get('age', type=int)
    month = request.args.get('month', '')
    try:
        ensure_age_notifications()
    except Exception:
        logger.warning('到龄提醒补生成失败', exc_info=True)
    return jsonify(list_age_notice(age=age, month=month))
