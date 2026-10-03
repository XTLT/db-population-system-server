"""DibaoPayment 模型。"""
from sqlalchemy import Column, String
from .._base import Base


class DibaoPayment(Base):
    __tablename__ = "dibao_payment"

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
    gender = Column(String, default="")  # 性别
    family_members = Column(String, default="")  # 共同生活家庭成员
    family_count = Column(String, default="")  # 享受保障人口数
    base_amount = Column(String, default="")  # 家庭最低生活基本保障金
    special_amount = Column(String, default="")  # 家庭特殊困难补助金
    adjust_amount = Column(String, default="")  # 家庭调剂金额
    special_situation = Column(String, default="")  # 特殊困难情形（分类施保）
    special_subsidy = Column(String, default="")  # 特殊困难补助金
    start_time = Column(String, default="")  # 初始享受时间
    issue_month = Column(String, default="")  # 始发年月
    import_time = Column(String, default="")
    import_source = Column(String, default="")  # 导入来源文件名

