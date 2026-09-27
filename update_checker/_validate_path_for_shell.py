def _validate_path_for_shell(path: str) -> bool:
    """验证路径是否安全可用于shell操作

    防止命令注入：检查路径是否包含危险字符
    """
    dangerous_chars = ['$', '`', '"', "'", '\\', '\n', '\r', ';', '&', '|', '<', '>', '(', ')']
    return not any(char in path for char in dangerous_chars)
