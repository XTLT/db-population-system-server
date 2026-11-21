"""AgeNoticeHandled 模型：到龄提醒里"已办理"的人员标记。"""

from sqlalchemy import Column, Integer, String

from .._base import Base


class AgeNoticeHandled(Base):
    __tablename__ = "age_notice_handled"

    # person_id + age_group + YYYY-MM，同一个人同一月同一档只记一次
    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    person_name = Column(String, default="")
    id_card = Column(String, default="")
    age_group = Column(Integer, default=60)
    target_month = Column(String, default="")  # YYYY-MM
    handled_at = Column(String, default="")
    handled_by = Column(String, default="")
