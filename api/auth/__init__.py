import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Blueprint

from database import get_session, User, add_operation_log
from utils.security import (
    create_token, remove_token, require_auth,
    DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, hash_password, verify_password
)
from utils.response import get_json_data, safe_exception
from utils import validate_username, validate_real_name
from config import TOKEN_EXPIRY_HOURS, LOGIN_LOCK_MINUTES
from database import validate_password, create_user, get_all_users


bp = Blueprint('auth', __name__)

from ._ensure_default_admin import _ensure_default_admin
from . import status
from . import health
from . import init
from . import login
from . import logout
from . import check_token
from . import change_password
from . import create_admin
