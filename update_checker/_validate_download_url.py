from ._constants import ALLOWED_DOMAINS


def _validate_download_url(url: str) -> bool:
    """
    验证下载URL是否安全

    Args:
        url: 下载URL

    Returns:
        是否为安全的URL
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # 必须使用HTTPS
        if parsed.scheme != 'https':
            return False

        # 检查域名
        domain = parsed.netloc.lower()
        for allowed in ALLOWED_DOMAINS:
            if domain == allowed or domain.endswith('.' + allowed):
                return True

        return False

    except Exception:
        return False
