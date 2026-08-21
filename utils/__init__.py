# 工具函数模块
from .security import (
    hash_password, 
    verify_password, 
    require_auth, 
    create_token,
    get_token_data,
    remove_token,
    _tokens,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
    check_id_card_rate_limit
)
from .response import safe_error, get_json_data
from .common import (
    calculate_age,
    clean_filename,
    validate_photo_filename,
    find_existing_photo,
    has_any_photo,
    get_photo_base_name,
    safe_str,
    calculate_enrollment_date
)

# 从 server/utils.py 导入验证函数
import os
import importlib.util
_utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils.py')
_spec = importlib.util.spec_from_file_location('server_utils', _utils_path)
_server_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_server_utils)

escape_like = _server_utils.escape_like
validate_id_card = _server_utils.validate_id_card
validate_phone = _server_utils.validate_phone
validate_username = _server_utils.validate_username
validate_year = _server_utils.validate_year
validate_real_name = _server_utils.validate_real_name

__all__ = [
    # security
    'hash_password',
    'verify_password',
    'require_auth',
    'create_token',
    'get_token_data',
    'remove_token',
    '_tokens',
    'DEFAULT_ADMIN_USERNAME',
    'DEFAULT_ADMIN_PASSWORD',
    'check_id_card_rate_limit',
    # response
    'safe_error',
    'get_json_data',
    # common
    'calculate_age',
    'clean_filename',
    'validate_photo_filename',
    'find_existing_photo',
    'has_any_photo',
    'get_photo_base_name',
    'safe_str',
    'calculate_enrollment_date',
    # validation
    'escape_like',
    'validate_id_card',
    'validate_phone',
    'validate_username',
    'validate_year',
    'validate_real_name'
]
