"""LandSubsidy 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class LandSubsidy(Base):
    __tablename__ = "land_subsidy"

    id = Column(String, primary_key=True)
    person_id = Column(String, default="")
    id_card = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    year = Column(String, default="", index=True)  # 补贴年份
    land_area = Column(String, default="")  # 土地面积
    subsidy_amount = Column(String, default="")  # 补贴金额
    certified_area = Column(String, default="")  # 确权面积
    subsidy_area = Column(String, default="")  # 补贴面积
    base_standard = Column(String, default="")  # 基础标准
    rape_area = Column(String, default="")  # 油菜面积
    rape_amount = Column(String, default="")  # 油菜金额
    total_amount = Column(String, default="")  # 总金额
    phone = Column(String, default="")  # 电话号码
    bank_account = Column(String, default="")  # 银行账号
    bank_name = Column(String, default="")  # 金融机构
    land_time = Column(String, default="")  # 上账时间
    rape_standard = Column(String, default="")  # 油菜标准
    created_at = Column(String, default="")  # 创建时间
    import_time = Column(String, default="")

