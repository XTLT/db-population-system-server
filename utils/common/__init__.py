# utils/common 包 — 向后兼容 shim
from .calculate_age import calculate_age
from .clean_filename import clean_filename
from .validate_photo_filename import validate_photo_filename
from .find_existing_photo import find_existing_photo
from .has_any_photo import has_any_photo
from .get_photo_base_name import get_photo_base_name
from .safe_str import safe_str
from .calculate_enrollment_date import calculate_enrollment_date
from .escape_like import escape_like
from .validate_id_card import validate_id_card
from .validate_phone import validate_phone
from .validate_username import validate_username
from .validate_year import validate_year
from .validate_real_name import validate_real_name

__all__ = [
    'calculate_age',
    'clean_filename',
    'validate_photo_filename',
    'find_existing_photo',
    'has_any_photo',
    'get_photo_base_name',
    'safe_str',
    'calculate_enrollment_date',
    'escape_like',
    'validate_id_card',
    'validate_phone',
    'validate_username',
    'validate_year',
    'validate_real_name',
]
