import re


def _parse_version(tag_name):
    """从tag解析版本号"""
    match = re.search(r'v?(\d+)\.(\d+)\.(\d+)', tag_name, re.IGNORECASE)
    if match:
        major, minor, patch = match.groups()
        code = int(major) * 10000 + int(minor) * 100 + int(patch)
        return code, f'{major}.{minor}.{patch}'
    return None, None
