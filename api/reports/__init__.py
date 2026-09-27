from flask import Blueprint

bp = Blueprint('reports', __name__)

from . import api_create_custom_report  # noqa: E402,F401
from . import api_get_custom_reports  # noqa: E402,F401
from . import api_get_custom_report  # noqa: E402,F401
from . import api_update_custom_report  # noqa: E402,F401
from . import api_delete_custom_report  # noqa: E402,F401
from . import api_generate_report  # noqa: E402,F401
