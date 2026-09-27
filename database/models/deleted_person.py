"""DeletedPerson 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class DeletedPerson(Base):
    __tablename__ = "deleted_persons"

    id = Column(String, primary_key=True)
    original_id = Column(String, nullable=False)
    hu_hao = Column(String, nullable=False)
    id_card = Column(String, nullable=False)
    name = Column(String, nullable=False)
    age = Column(String, default="")
    address = Column(String, default="")
    relation = Column(String, default="")
    is_dead = Column(String, default="否")
    phone = Column(String, default="")
    remark = Column(String, default="")
    poor_type = Column(String, default="")
    disability = Column(String, default="")
    disability_type = Column(String, default="")
    dis_level = Column(String, default="")
    dibao = Column(String, default="")
    tekun = Column(String, default="")
    tekun_type = Column(String, default="")
    jisheng = Column(String, default="")
    social_card1 = Column(String, default="")
    social_card2 = Column(String, default="")
    social_card3 = Column(String, default="")
    is_migrated = Column(String, default="否")
    migration_date = Column(String, default="")
    migration_place = Column(String, default="")
    migration_reason = Column(String, default="")
    deleted_at = Column(String, nullable=False)

