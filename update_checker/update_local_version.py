from .load_local_config import load_local_config
from .save_local_config import save_local_config


def update_local_version(version_info: dict, app_type: str = "server"):
    """更新本地版本记录"""
    config = load_local_config()
    if app_type == "desktop":
        config["current_version"] = version_info.get("desktop_version", config.get("current_version", "1.0.0"))
        config["version_code"] = version_info.get("desktop_version_code", config.get("version_code", 1) + 1)
    else:
        config["current_version"] = version_info.get("server_version", config.get("current_version", "1.0.0"))
        config["version_code"] = version_info.get("server_version_code", config.get("version_code", 1) + 1)
    save_local_config(config)
