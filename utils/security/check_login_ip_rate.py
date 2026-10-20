"""登录 IP 级限流：跨 gunicorn worker 共享（DB 存储）。

策略：
- 同一 IP 连续登录失败 IP_LOCK_ATTEMPTS 次，锁定 IP_LOCK_MINUTES 分钟
- 登录成功清除该 IP 的失败记录
- 与账号级锁定（5 次锁号）叠加，防止换账号批量爆破
"""
from datetime import datetime, timedelta

from database import get_session
from database.models.login_ip_lock import LoginIpLock

IP_LOCK_ATTEMPTS = 10
IP_LOCK_MINUTES = 15


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_login_ip_locked(ip: str) -> tuple:
    """返回 (是否锁定, 剩余分钟数)。"""
    session = get_session()
    try:
        rec = session.query(LoginIpLock).filter_by(ip=ip).first()
        if rec and rec.locked_until:
            try:
                lock_time = datetime.strptime(rec.locked_until, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < lock_time:
                    remaining = int((lock_time - datetime.now()).total_seconds() / 60) + 1
                    return True, remaining
            except Exception:
                pass
        return False, 0
    finally:
        session.close()


def record_login_ip_fail(ip: str):
    session = get_session()
    try:
        rec = session.query(LoginIpLock).filter_by(ip=ip).first()
        if not rec:
            rec = LoginIpLock(ip=ip, failed_count=0)
            session.add(rec)
        rec.failed_count = (rec.failed_count or 0) + 1
        rec.updated_at = _now_str()
        if rec.failed_count >= IP_LOCK_ATTEMPTS:
            rec.locked_until = (datetime.now() + timedelta(minutes=IP_LOCK_MINUTES)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            rec.failed_count = 0
        session.commit()
    finally:
        session.close()


def clear_login_ip_fail(ip: str):
    session = get_session()
    try:
        rec = session.query(LoginIpLock).filter_by(ip=ip).first()
        if rec:
            session.delete(rec)
        session.commit()
    finally:
        session.close()
