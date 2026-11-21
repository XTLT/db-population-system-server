from flask import Blueprint

bp = Blueprint('notifications', __name__)

from . import api_get_notifications  # noqa: E402,F401
from . import api_get_unread_count  # noqa: E402,F401
from . import api_mark_notification_read  # noqa: E402,F401
from . import api_send_notification  # noqa: E402,F401
from . import api_age_notice  # noqa: E402,F401
from . import api_mark_age_notice_handled  # noqa: E402,F401
