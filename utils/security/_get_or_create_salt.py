import os
import secrets
import logging

logger = logging.getLogger('population_system')

# Token 哈希盐值文件路径
_SALT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.token_salt')


def _get_or_create_salt() -> str:
    """获取或创建 Token 哈希盐值"""
    salt_file = os.path.abspath(_SALT_FILE)

    # 尝试读取现有 salt
    if os.path.exists(salt_file):
        try:
            with open(salt_file, 'r') as f:
                salt = f.read().strip()
                if len(salt) >= 32:  # 确保长度足够
                    return salt
        except Exception as e:
            logger.warning(f"读取Token盐值失败: {e}")

    # 生成新的 salt
    salt = secrets.token_hex(32)
    try:
        with open(salt_file, 'w') as f:
            f.write(salt)
        os.chmod(salt_file, 0o600)  # 设置权限，仅所有者可读写
        logger.info("已生成新的Token哈希盐值")
    except Exception as e:
        logger.error(f"保存Token盐值失败: {e}")

    return salt
