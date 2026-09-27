import hashlib
from . import _base


def verify_password(password: str, password_hash: str) -> tuple[bool, bool]:
    """验证密码

    Returns:
        (is_valid, needs_rehash): 验证结果和是否需要重新哈希
    """
    try:
        # Argon2 格式: argon2:$argon2id$...
        if password_hash.startswith("argon2:"):
            if not _base.ARGON2_AVAILABLE:
                _base.logger.error("密码使用 Argon2 哈希但 argon2-cffi 未安装")
                return False, False

            actual_hash = password_hash[7:]  # 去掉 "argon2:" 前缀
            try:
                _base._ph.verify(actual_hash, password)
                # 检查是否需要重新哈希（参数可能已更新）
                needs_rehash = _base._ph.check_needs_rehash(actual_hash)
                return True, needs_rehash
            except (_base.VerifyMismatchError, _base.VerificationError):
                return False, False

        # SHA256 格式: sha256:salt:hash 或旧格式 salt:hash
        if password_hash.startswith("sha256:"):
            parts = password_hash.split(":")
            if len(parts) == 3:
                _, salt, stored_hash = parts
            else:
                return False, False
        else:
            # 旧格式兼容: salt:hash
            parts = password_hash.split(":")
            if len(parts) != 2:
                return False, False
            salt, stored_hash = parts

        # SHA256 验证
        password_sha256 = hashlib.sha256(password.encode()).hexdigest()
        new_format_hash = hashlib.sha256((salt + password_sha256).encode()).hexdigest()
        if new_format_hash == stored_hash:
            return True, True  # 旧格式，需要重新哈希

        old_format_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        if old_format_hash == stored_hash:
            return True, True  # 旧格式，需要重新哈希

        return False, False
    except Exception as e:
        _base.logger.error(f"密码验证异常: {e}")
        return False, False
