from ._constants import REQUIRE_SIGNATURE
from .calculate_sha256 import calculate_sha256


def verify_file(filepath: str, expected_checksum: str) -> bool:
    """
    验证文件完整性

    Args:
        filepath: 文件路径
        expected_checksum: 预期的校验和（格式：sha256:xxxxxx）

    Returns:
        是否验证通过

    安全策略：
        1. 必须提供SHA256校验和
        2. 格式必须为 sha256:xxxxxx
        3. 计算并比较SHA256值
    """
    # 如果启用了强制签名要求，不允许跳过验证
    if REQUIRE_SIGNATURE:
        if not expected_checksum or not expected_checksum.startswith("sha256:"):
            return False
    else:
        if not expected_checksum or not expected_checksum.startswith("sha256:"):
            return True  # 未配置校验，跳过验证（不推荐）

    expected_hash = expected_checksum[7:]
    actual_hash = calculate_sha256(filepath)
    return expected_hash == actual_hash
