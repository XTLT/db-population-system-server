import json
import requests
from .load_local_config import load_local_config
from ._constants import VERSION_URLS
from ._validate_url import _validate_url


def check_update(app_type: str = "desktop"):
    """
    检查是否有新版本

    Args:
        app_type: 应用类型 "desktop" 或 "server"

    Returns:
        (版本信息, 错误信息) - 如果有新版本返回版本信息，否则返回 (None, "")
    """
    config = load_local_config()
    current_code = config.get("version_code", 1)

    try:
        data = None
        last_error = None
        for url in VERSION_URLS:
            # 验证URL是否在白名单中
            if not _validate_url(url):
                last_error = f"更新源不在白名单中: {url}"
                continue

            try:
                # 启用证书验证
                resp = requests.get(url, timeout=10, verify=True)
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                last_error = e
                continue

        if data is None:
            return None, f"所有更新源均无法访问: {last_error}"

        # 根据应用类型获取对应的版本信息
        if app_type == "desktop":
            latest_code = data.get("desktop_version_code", data.get("version_code", 0))
        else:
            latest_code = data.get("server_version_code", data.get("version_code", 0))

        # 版本比较
        if latest_code > current_code:
            return data, ""
        else:
            return None, ""

    except requests.exceptions.RequestException as e:
        return None, f"检查更新失败: {e}"
    except json.JSONDecodeError as e:
        return None, f"解析版本信息失败: {e}"
    except Exception as e:
        return None, f"未知错误: {e}"
