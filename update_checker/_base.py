import os
import sys
import urllib3

# 禁用不安全的警告（仅用于调试）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from ._get_config_dir import _get_config_dir

CONFIG_DIR = _get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "version_config.json")
DOWNLOAD_DIR = os.path.join(CONFIG_DIR, "downloads")
