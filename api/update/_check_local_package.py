# -*- coding: utf-8 -*-
"""读取服务器本地更新包元数据（updates/<type>/version.json）。

服务器作为更新主源：发布者把 exe/apk 放到 updates/<type>/ 目录，
并写好 version.json 后，客户端即可从服务器直接检查更新与下载。
"""
import json
import os

from config import UPDATES_DIR


def _type_dir(app_type: str) -> str:
    return os.path.join(UPDATES_DIR, app_type)


def get_local_package_meta(app_type: str):
    """读取本地更新包元数据。

    返回 dict（含 latest_version/version_code/file/file_size/sha256/
    release_notes/updated_at），文件或元数据不存在时返回 None。
    """
    meta_path = os.path.join(_type_dir(app_type), "version.json")
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        fname = meta.get("file", "")
        if not fname:
            return None
        full = os.path.join(_type_dir(app_type), fname)
        if not os.path.exists(full):
            return None
        # 补齐实际文件大小（若元数据未写或过期）
        real_size = os.path.getsize(full)
        meta["file_size"] = int(meta.get("file_size") or 0) or real_size
        meta["_full_path"] = full
        return meta
    except Exception:
        return None
