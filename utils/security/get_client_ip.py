# utils/security/get_client_ip.py
from flask import request


def get_client_ip():
    """取客户端真实 IP：优先 X-Forwarded-For（stunnel xforwarded=yes 注入），否则 remote_addr。

    背景：gunicorn 绑 127.0.0.1:5001，stunnel 5000→5001 TCP 转发，
    不配 xforwarded 时 request.remote_addr 恒为 127.0.0.1，操作日志无法区分来源。
    stunnel 5.68 在 [population] 段配置 xforwarded = yes 后向 HTTP 流注入
    X-Forwarded-For: <客户端IP>；多级代理取最左侧（原始客户端）IP。
    """
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        ip = xff.split(',')[0].strip()
        if ip:
            return ip
    return request.remote_addr or ''
