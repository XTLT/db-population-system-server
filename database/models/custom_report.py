"""CustomReport 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class CustomReport(Base):
    __tablename__ = "custom_reports"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    report_type = Column(String, nullable=False)  # person, student, subsidy
    dimensions = Column(String, default="")  # JSON: 统计维度列表
    date_range = Column(String, default="")  # JSON: {start, end}
    chart_type = Column(String, default="bar")  # bar, line, pie, radar
    filters = Column(String, default="")  # JSON: 筛选条件
    created_at = Column(String, nullable=False)
    updated_at = Column(String, default="")

