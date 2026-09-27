"""StudentEducation 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class StudentEducation(Base):
    __tablename__ = "student_education"

    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    id_card = Column(String, nullable=False, index=True)
    school_name = Column(String, default="")
    grade = Column(String, default="")
    class_name = Column(String, default="")
    guardian = Column(String, default="")
    guardian_phone = Column(String, default="")
    is_left_behind = Column(String, default="否")
    student_status = Column(String, default="")
    enrollment_date = Column(String, default="")
    graduation_date = Column(String, default="")

