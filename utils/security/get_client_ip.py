# utils/security/get_client_ip.py
from flask import request


def _normalize(ip):
    """把 IPv4-mapped IPv6 地址(::ffff:192.168.9.32)还原成 192.168.9.32。

    双栈监听([::]:5000)下，IPv4 客户端在 socket 上表现为 IPv4-mapped IPv6，
    直接入日志会变成 ::ffff:x.x.x.x，这里统一规范化。
    """
    if not ip:
        return ''
    ip = ip.strip()
    if ip.startswith('::ffff:') and '.' in ip:
        return ip[7:]
    return ip


def get_client_ip():
    """取客户端真实 IP。

    优先 X-Forwarded-For（反向代理/VPN 注入，取最左原始客户端），
    否则用 request.remote_addr（gunicorn 直连 TLS 时即真实客户端 IP）。
    """
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        ip = _normalize(xff.split(',')[0])
        if ip:
            return ip
    return _normalize(request.remote_addr or '')
