"""EducationHistory 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class EducationHistory(Base):
    __tablename__ = "education_history"

    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    id_card = Column(String, nullable=False)
    school_name = Column(String, default="")
    grade = Column(String, default="")
    class_name = Column(String, default="")
    student_status = Column(String, default="")
    change_date = Column(String, default="")
    change_reason = Column(String, default="")

