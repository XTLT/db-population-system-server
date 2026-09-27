"""Person 模型。"""
from sqlalchemy import Column, String, Index
from .._base import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(String, primary_key=True)
    hu_hao = Column(String, nullable=False, index=True)
    id_card = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
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
    updated_at = Column(String, default="")
    land_area = Column(String, default="")
    land_area_change_reason = Column(String, default="")
    land_area_change_time = Column(String, default="")
    local_welfare_forest_area = Column(String, default="")
    local_welfare_forest_change_reason = Column(String, default="")
    local_welfare_forest_change_time = Column(String, default="")
    national_welfare_forest_area = Column(String, default="")
    national_welfare_forest_change_reason = Column(String, default="")
    national_welfare_forest_change_time = Column(String, default="")
    commercial_forest_area = Column(String, default="")
    commercial_forest_change_reason = Column(String, default="")
    commercial_forest_change_time = Column(String, default="")

    __table_args__ = (
        Index("idx_name_hu_hao", "name", "hu_hao"),
    )

