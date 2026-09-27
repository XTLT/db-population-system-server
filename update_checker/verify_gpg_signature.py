import os
import subprocess
import tempfile
import requests
from ._validate_download_url import _validate_download_url
from ._constants import GPG_KEY_FINGERPRINTS


def verify_gpg_signature(filepath: str, signature_url: str = None, signature_data: bytes = None):
    """
    验证 GPG 签名

    Args:
        filepath: 要验证的文件路径
        signature_url: 签名文件URL（可选）
        signature_data: 签名数据（可选）

    Returns:
        (是否验证通过, 错误信息)
    """
    try:
        # 获取签名数据
        if signature_data is None and signature_url:
            # 验证签名URL是否在白名单中
            if not _validate_download_url(signature_url):
                return False, "签名文件URL不在白名单中"
            resp = requests.get(signature_url, timeout=30, verify=True)
            resp.raise_for_status()
            signature_data = resp.content

        if signature_data is None:
            return False, "未提供签名数据"

        # 写入临时签名文件
        with tempfile.NamedTemporaryFile(suffix='.sig', delete=False) as sig_file:
            sig_file.write(signature_data)
            sig_path = sig_file.name

        try:
            # 使用 gpg 验证签名
            result = subprocess.run(
                ['gpg', '--verify', sig_path, filepath],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # 检查签名者指纹是否在白名单中
                if GPG_KEY_FINGERPRINTS:
                    # 提取签名者指纹
                    fingerprint_result = subprocess.run(
                        ['gpg', '--verify', '--status-fd', '1', sig_path, filepath],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    # 检查指纹是否在白名单
                    for fingerprint in GPG_KEY_FINGERPRINTS:
                        if fingerprint in fingerprint_result.stdout:
                            return True, ""

                    return False, "签名者GPG密钥不在信任列表中"

                return True, ""
            else:
                return False, f"GPG签名验证失败: {result.stderr}"

        finally:
            os.unlink(sig_path)

    except FileNotFoundError:
        return False, "系统未安装GPG，无法验证签名"
    except subprocess.TimeoutExpired:
        return False, "签名验证超时"
    except Exception as e:
        return False, f"签名验证错误: {e}"
