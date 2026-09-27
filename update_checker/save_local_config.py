import os
import json
from ._base import CONFIG_FILE


def save_local_config(config):
    """保存本地版本配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
