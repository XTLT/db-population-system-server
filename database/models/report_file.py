"""ReportFile 模型。"""
from sqlalchemy import Column, String, Integer
from .._base import Base


class ReportFile(Base):
    __tablename__ = "report_files"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    upload_user_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    upload_time = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

