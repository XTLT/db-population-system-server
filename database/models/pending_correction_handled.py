"""PendingCorrectionHandled 模型：待核销清单里"已核销"的人员标记。"""

from sqlalchemy import Column, Integer, String

from .._base import Base


class PendingCorrectionHandled(Base):
    __tablename__ = "pending_correction_handled"

    # 一个人一条，重复核销只更新快照与时间
    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    person_name = Column(String, default="")
    id_card = Column(String, default="")
    module_labels = Column(String, default="")  # 核销时挂着的补贴模块，逗号分隔
    module_count = Column(Integer, default=0)
    total_amount = Column(String, default="")
    handled_at = Column(String, default="")
    handled_by = Column(String, default="")
