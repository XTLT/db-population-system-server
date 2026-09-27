"""User 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    real_name = Column(String, default="")
    role = Column(String, default="user")
    is_active = Column(String, default="是")
    is_default = Column(String, default="否")
    created_at = Column(String, default="")
    last_login = Column(String, default="")
    login_attempts = Column(String, default="0")
    locked_until = Column(String, default="")

