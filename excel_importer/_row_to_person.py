from database import Person
from utils import safe_str, calculate_age
from excel_area_fields import (
    get_land_area_from_row,
    get_local_welfare_forest_from_row,
    get_national_welfare_forest_from_row,
    get_commercial_forest_from_row,
)


def _row_to_person(row, idx) -> Person:
    id_card = safe_str(row.get("身份证号", ""))
    return Person(
        id=f"p_{idx}_{id_card}",
        hu_hao=safe_str(row.get("户号", "")),
        id_card=id_card,
        name=safe_str(row.get("姓名", "")),
        age=calculate_age(id_card),
        address=safe_str(row.get("地址", "")),
        relation=safe_str(row.get("与户主关系", "")),
        is_dead=safe_str(row.get("是否死亡", "否")),
        phone=safe_str(row.get("电话", "")),
        remark=safe_str(row.get("备注", "")),
        poor_type=safe_str(row.get("脱贫户或监测户", "")),
        disability=safe_str(row.get("残疾", "")),
        dis_level=safe_str(row.get("残疾等级", "")),
        dibao=safe_str(row.get("低保", "")),
        tekun=safe_str(row.get("特困供养", "")),
        tekun_type=safe_str(row.get("供养类型", "")),
        jisheng=safe_str(row.get("是否计生家庭", "")),
        social_card1=safe_str(row.get("社保卡号1", "")),
        social_card2=safe_str(row.get("社保卡号2", "")),
        social_card3=safe_str(row.get("社保卡号3", "")),
        land_area=get_land_area_from_row(row),
        local_welfare_forest_area=get_local_welfare_forest_from_row(row),
        national_welfare_forest_area=get_national_welfare_forest_from_row(row),
        commercial_forest_area=get_commercial_forest_from_row(row),
    )
