import os
import json
from ._base import CONFIG_FILE


def load_local_config():
    """加载本地版本配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_version": "1.0.0", "version_code": 1}
