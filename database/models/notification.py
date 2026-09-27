"""Notification 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    notification_type = Column(String, default="system")  # system, business
    target_user = Column(String, default="")  # 空=所有用户，指定用户名=特定用户
    sender_id = Column(String, default="")
    sender_name = Column(String, default="")
    is_read = Column(String, default="否")
    created_at = Column(String, nullable=False)
    read_at = Column(String, default="")

