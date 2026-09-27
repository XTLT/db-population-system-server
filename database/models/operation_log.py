"""OperationLog 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)
    operation_target = Column(String, default="")
    ip_address = Column(String, default="")
    client_type = Column(String, default="")
    created_at = Column(String, nullable=False)
    is_high_risk = Column(String, default="否")

