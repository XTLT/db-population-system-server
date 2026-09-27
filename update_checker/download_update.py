import os
import sys
import requests
from ._base import DOWNLOAD_DIR
from ._constants import REQUIRE_SIGNATURE, REQUIRE_GPG_SIGNATURE
from ._validate_download_url import _validate_download_url
from .verify_file import verify_file
from .verify_gpg_signature import verify_gpg_signature
from .verify_windows_code_signature import verify_windows_code_signature


def download_update(version_info: dict, progress_callback=None):
    """
    下载更新文件

    Args:
        version_info: 版本信息
        progress_callback: 进度回调 (downloaded_bytes, total_bytes)

    Returns:
        (文件路径, 错误信息)

    安全要求：
        1. 下载URL必须在白名单域名中
        2. 必须提供SHA256校验和
        3. 下载完成后验证文件完整性
    """
    urls = []
    if version_info.get("server_download_url"):
        urls.append(version_info["server_download_url"])
    if version_info.get("download_url"):
        urls.append(version_info["download_url"])

    if not urls:
        return None, "未找到下载链接"

    # 检查是否有签名信息
    has_checksum = False
    checksum_fields = ["server_checksum", "checksum", "sha256", "sha256_checksum"]
    for field in checksum_fields:
        if version_info.get(field):
            has_checksum = True
            break

    if REQUIRE_SIGNATURE and not has_checksum:
        return None, "安全错误：更新文件未提供SHA256校验和，拒绝下载"

    filename = "update.exe"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    for url in urls:
        # 验证下载URL是否安全
        if not _validate_download_url(url):
            continue

        try:
            # 启用证书验证
            resp = requests.get(url, stream=True, timeout=300, verify=True)
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)

            # 验证文件完整性
            for field in checksum_fields:
                checksum = version_info.get(field)
                if checksum:
                    if not verify_file(filepath, checksum):
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        return None, "文件校验失败：SHA256不匹配，可能被篡改"
                    break

            # 验证 GPG 签名（如果提供）
            gpg_signature_url = version_info.get("gpg_signature_url")
            gpg_signature = version_info.get("gpg_signature")
            if gpg_signature_url or gpg_signature:
                gpg_valid, gpg_error = verify_gpg_signature(
                    filepath,
                    signature_url=gpg_signature_url,
                    signature_data=gpg_signature.encode() if gpg_signature else None
                )
                if not gpg_valid:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None, f"GPG签名验证失败: {gpg_error}"
            elif REQUIRE_GPG_SIGNATURE:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None, "安全错误：未提供GPG签名，拒绝更新"

            # 验证 Windows 代码签名（如果是可执行文件）
            if filepath.endswith('.exe') and sys.platform == 'win32':
                code_valid, code_error = verify_windows_code_signature(filepath)
                if not code_valid:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None, f"代码签名验证失败: {code_error}"

            return filepath, ""

        except requests.exceptions.RequestException:
            if os.path.exists(filepath):
                os.remove(filepath)
            continue

    return None, "所有下载源均失败或不在白名单中"
