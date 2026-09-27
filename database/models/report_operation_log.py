"""ReportOperationLog 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class ReportOperationLog(Base):
    __tablename__ = "report_operation_logs"
    id = Column(String, primary_key=True)
    report_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)
    operation_detail = Column(String, default="")
    ip_address = Column(String, default="")
    client_type = Column(String, default="")
    created_at = Column(String, nullable=False)

