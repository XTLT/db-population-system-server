"""GET /api/persons/deleted：列出已删除人员。"""

from flask import jsonify
from utils.security import require_auth

from database import get_deleted_persons
from .deleted_to_dict import deleted_to_dict


@require_auth
def api_list_deleted():
    deleted = get_deleted_persons()
    return jsonify([deleted_to_dict(d) for d in deleted])
