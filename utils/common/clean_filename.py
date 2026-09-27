import re


def clean_filename(name: str, max_length: int = 100) -> str:
    """清理文件名，移除非法字符"""
    # 移除非法字符
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # 限制长度
    if len(name) > max_length:
        name = name[:max_length]
    return name
