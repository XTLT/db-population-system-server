"""HouseBuildApp 模型：农村宅基地和建房（规划许可）申请/审批记录。

一户可以有多条（翻建、扩建、异址新建分别建记录），保留历史。
申请表与审批表的数据都落在这一张表里，申请宅基地面积用独立列存储
（`apply_land_area` 原文 + `apply_area_num` 数值，便于按村/按年汇总），
批准面积同理（`approval_land_area` / `approval_area_num`）。
"""

from sqlalchemy import Column, Float, Index, String, Text

from .._base import Base


class HouseBuildApp(Base):
    __tablename__ = "house_build_app"

    id = Column(String, primary_key=True)
    app_no = Column(String, default="", index=True)  # 申请编号，如 HB-2026-0001
    person_id = Column(String, default="", index=True)

    # ===== 申请人信息（申请表）=====
    owner_name = Column(String, nullable=False, index=True)
    owner_gender = Column(String, default="")
    owner_age = Column(String, default="")
    owner_phone = Column(String, default="")
    owner_id_card = Column(String, default="", index=True)
    owner_hukou = Column(String, default="")  # 户口所在地
    hu_hao = Column(String, default="", index=True)
    group_name = Column(String, default="")

    # ===== 拟申请宅基地及建房情况（申请表）=====
    apply_land_area = Column(String, default="")   # 宅基地面积（m²，原样）
    apply_area_num = Column(Float, default=0.0)    # 同上，数值，便于汇总
    building_area = Column(String, default="")     # 建筑面积
    cert_no = Column(String, default="")           # 权属证书号
    current_disposal = Column(String, default="")  # 现宅基地处置情况：保留/退给村集体/其他
    current_disposal_other = Column(String, default="")  # 其他说明
    current_land_area = Column(String, default="") # 现宅基地面积
    foundation_area = Column(String, default="")   # 房基占地面积
    east_to = Column(String, default="")
    south_to = Column(String, default="")
    west_to = Column(String, default="")
    north_to = Column(String, default="")
    build_type = Column(String, default="")        # 原址翻建/改扩建/异址新建
    land_type = Column(String, default="")         # 建设用地/未利用地/农用地
    house_floor_area = Column(String, default="")  # 住房建筑面积
    floors = Column(String, default="")            # 建筑层数
    building_height = Column(String, default="")   # 建筑高度
    neighbor_opinion = Column(String, default="")  # 是否征求相邻权利人意见：是/否
    design_plan = Column(String, default="")       # 是否有住宅设计方案/通用图集：是/否
    apply_reason = Column(String, default="")
    village_opinion = Column(String, default="")   # 村集体经济组织或村委会意见
    village_leader = Column(String, default="")    # 负责人
    village_date = Column(String, default="")      # 日期
    # 申请人移动端手写签名（PNG/JPEG base64，仅申请表 PDF 嵌图；Excel 保留空白手签位）
    applicant_signature = Column(Text, default="")
    applicant_signature_at = Column(String, default="")

    # ===== 拟批准宅基地及建房情况（审批表）=====
    approval_land_area = Column(String, default="")
    approval_area_num = Column(Float, default=0.0)
    approval_foundation_area = Column(String, default="")
    approval_address = Column(String, default="")  # 地址
    approval_build_type = Column(String, default="")
    approval_land_type = Column(String, default="")
    approval_house_floor_area = Column(String, default="")
    approval_floors = Column(String, default="")
    approval_height = Column(String, default="")

    # 五家机构审批意见 JSON：
    # {"natural": {...}, "housing": {...}, "agriculture": {...},
    #  "other": {...}, "government": {...}}，每组 {opinion, leader, date}
    approvals_json = Column(Text, default="")

    status = Column(String, default="draft", index=True)  # draft/submitted/approved
    remark = Column(String, default="")
    created_at = Column(String, default="")
    updated_at = Column(String, default="")
    created_by = Column(String, default="")
    updated_by = Column(String, default="")

    __table_args__ = (
        Index("idx_hb_owner", "owner_name", "owner_id_card"),
        Index("idx_hb_area", "apply_area_num"),
    )


class HouseBuildMember(Base):
    """申请表的家庭成员信息（每个申请各自一份，按 app_id 挂）。"""

    __tablename__ = "house_build_member"

    id = Column(String, primary_key=True)
    app_id = Column(String, nullable=False, index=True)
    seq = Column(String, default="")  # 行序，字符串便于原样保存
    name = Column(String, default="")
    age = Column(String, default="")
    relation = Column(String, default="")
    id_card = Column(String, default="")
    hukou = Column(String, default="")
