from ._constants import ALLOWED_DOMAINS


def _validate_url(url: str) -> bool:
    """
    验证URL是否在允许的白名单域名中

    Args:
        url: 要验证的URL

    Returns:
        是否为允许的域名
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # 必须使用HTTPS
        if parsed.scheme != 'https':
            return False

        # 检查域名是否在白名单中
        domain = parsed.netloc.lower()
        for allowed in ALLOWED_DOMAINS:
            if domain == allowed or domain.endswith('.' + allowed):
                return True

        return False

    except Exception:
        return False
