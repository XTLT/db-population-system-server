import sys
import subprocess
from ._constants import CODE_SIGNING_CERTS


def verify_windows_code_signature(filepath: str):
    """
    验证 Windows 可执行文件的代码签名

    Args:
        filepath: 可执行文件路径

    Returns:
        (是否验证通过, 错误信息)
    """
    if sys.platform != 'win32':
        return True, "非Windows系统，跳过代码签名验证"

    if not filepath.endswith('.exe'):
        return True, "非可执行文件，跳过签名验证"

    # 安全检查：验证文件路径不包含危险字符
    dangerous_chars = ['$', '`', '"', "'", '\n', '\r', ';', '&', '|', '<', '>', '(', ')']
    if any(char in filepath for char in dangerous_chars):
        return False, "文件路径包含不安全字符"

    try:
        # 使用 PowerShell 验证代码签名
        # 注意：filepath 已经过安全检查，但仍需转义
        escaped_path = filepath.replace("'", "''")
        ps_script = f'''
        $sig = Get-AuthenticodeSignature '{escaped_path}'
        if ($sig.Status -eq "Valid") {{
            Write-Output "VALID"
            Write-Output $sig.SignerCertificate.Thumbprint
        }} else {{
            Write-Output "INVALID"
            Write-Output $sig.Status
        }}
        '''

        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        lines = result.stdout.strip().split('\n')

        if lines and lines[0] == 'VALID':
            # 如果配置了证书白名单，验证证书指纹
            if CODE_SIGNING_CERTS:
                cert_thumbprint = lines[1] if len(lines) > 1 else ""
                if cert_thumbprint in CODE_SIGNING_CERTS:
                    return True, ""
                else:
                    return False, f"代码签名证书不在信任列表中: {cert_thumbprint}"
            return True, ""
        else:
            status = lines[1] if len(lines) > 1 else "未知错误"
            return False, f"代码签名无效: {status}"

    except subprocess.TimeoutExpired:
        return False, "签名验证超时"
    except Exception as e:
        return False, f"签名验证错误: {e}"
