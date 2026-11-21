"""GET /api/notifications/age-notice：下月到龄名单（结构化，排除已办理）。"""

from flask import jsonify, request

from database import list_age_notice
from utils.security import require_auth
from . import bp


@bp.route('/age-notice', methods=['GET'])
@require_auth
def api_age_notice():
    age = request.args.get('age', type=int)
    month = request.args.get('month', '')
    return jsonify(list_age_notice(age=age, month=month))
