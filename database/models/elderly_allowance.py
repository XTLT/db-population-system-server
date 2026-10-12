"""ElderlyAllowance 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class ElderlyAllowance(Base):
    __tablename__ = "elderly_allowance"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    id_card = Column(String, default="", index=True)
    town = Column(String, default="")  # 所属乡镇
    village = Column(String, default="")  # 所属村
    period = Column(String, default="", index=True)  # 费款所属期/年月
    payment_status = Column(String, default="")  # 支付标志
    personal_code = Column(String, default="")  # 个人编号
    bank_account = Column(String, default="")
    amount = Column(String, default="")
    relation = Column(String, default="")  # 和申请人关系
    fail_reason = Column(String, default="")  # 失败原因
    phone = Column(String, default="")  # 手机号
    fold_no = Column(String, default="")  # 折号
    bank_name = Column(String, default="")  # 开户行
    area_address = Column(String, default="")  # 区划地址
    agent_manage = Column(String, default="")  # 代持代管
    householder_name = Column(String, default="")  # 户主姓名
    householder_id_card = Column(String, default="")  # 户主身份证号
    remark = Column(String, default="")  # 备注
    import_time = Column(String, default="")
    import_source = Column(String, default="")  # 导入来源文件名
