"""PensionInsurance 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class PensionInsurance(Base):
    __tablename__ = "pension_insurance"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    id_card = Column(String, default="", index=True)
    town = Column(String, default="")  # 所属乡镇
    village = Column(String, default="")  # 所属村
    period = Column(String, default="", index=True)  # 费款所属期/年月
    payment_status = Column(String, default="")  # 支付标志
    personal_code = Column(String, default="")  # 个人编号
    person_id = Column(String, default="")  # 享受定期待遇人员ID
    bank_account = Column(String, default="")
    amount = Column(String, default="")
    fail_reason = Column(String, default="")  # 失败原因
    import_time = Column(String, default="")
    import_source = Column(String, default="")  # 导入来源文件名

