"""登录 IP 限流模型：跨 gunicorn worker 共享（DB 存储）。"""
from sqlalchemy import Column, String, Integer
from .._base import Base


class LoginIpLock(Base):
    __tablename__ = "login_ip_locks"

    ip = Column(String, primary_key=True)
    failed_count = Column(Integer, default=0)
    locked_until = Column(String, default="")
    updated_at = Column(String, default="")
