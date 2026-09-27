"""Token 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class Token(Base):
    __tablename__ = "tokens"

    token = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    user_data = Column(String, nullable=False)  # JSON 格式的用户数据
    expires_at = Column(String, nullable=False)
    created_at = Column(String, default="")
    ip = Column(String, default="")

