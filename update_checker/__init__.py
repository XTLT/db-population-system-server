# update_checker 包 — 向后兼容 shim
from ._constants import (
    VERSION_URLS,
    ALLOWED_DOMAINS,
    AUTO_UPDATE_ENABLED,
    REQUIRE_SIGNATURE,
    REQUIRE_GPG_SIGNATURE,
    GPG_KEY_FINGERPRINTS,
    CODE_SIGNING_CERTS,
)
from ._get_config_dir import _get_config_dir
from ._base import CONFIG_DIR, CONFIG_FILE, DOWNLOAD_DIR
from ._validate_url import _validate_url
from ._validate_download_url import _validate_download_url
from .load_local_config import load_local_config
from .save_local_config import save_local_config
from .check_update import check_update
from .download_update import download_update
from .calculate_sha256 import calculate_sha256
from .verify_gpg_signature import verify_gpg_signature
from .verify_windows_code_signature import verify_windows_code_signature
from .verify_file import verify_file
from .update_local_version import update_local_version
from ._validate_path_for_shell import _validate_path_for_shell
from .apply_update import apply_update

__all__ = [
    'VERSION_URLS',
    'ALLOWED_DOMAINS',
    'AUTO_UPDATE_ENABLED',
    'REQUIRE_SIGNATURE',
    'REQUIRE_GPG_SIGNATURE',
    'GPG_KEY_FINGERPRINTS',
    'CODE_SIGNING_CERTS',
    '_get_config_dir',
    'CONFIG_DIR',
    'CONFIG_FILE',
    'DOWNLOAD_DIR',
    '_validate_url',
    '_validate_download_url',
    'load_local_config',
    'save_local_config',
    'check_update',
    'download_update',
    'calculate_sha256',
    'verify_gpg_signature',
    'verify_windows_code_signature',
    'verify_file',
    'update_local_version',
    '_validate_path_for_shell',
    'apply_update',
]
