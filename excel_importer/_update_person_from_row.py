from database import Person
from utils import safe_str, calculate_age
from excel_area_fields import (
    get_land_area_from_row_existing,
    get_local_welfare_forest_from_row_existing,
    get_national_welfare_forest_from_row_existing,
    get_commercial_forest_from_row_existing,
)


def _update_person_from_row(person: Person, row):
    person.hu_hao = safe_str(row.get("户号", person.hu_hao))
    person.name = safe_str(row.get("姓名", person.name))
    person.age = calculate_age(person.id_card)
    person.address = safe_str(row.get("地址", person.address))
    person.relation = safe_str(row.get("与户主关系", person.relation))
    person.is_dead = safe_str(row.get("是否死亡", person.is_dead))
    person.phone = safe_str(row.get("电话", person.phone))
    person.remark = safe_str(row.get("备注", person.remark))
    person.poor_type = safe_str(row.get("脱贫户或监测户", person.poor_type))
    person.disability = safe_str(row.get("残疾", person.disability))
    person.dis_level = safe_str(row.get("残疾等级", person.dis_level))
    person.disability_type = safe_str(row.get("残疾类型", person.disability_type))
    person.dibao = safe_str(row.get("低保", person.dibao))
    person.tekun = safe_str(row.get("特困供养", person.tekun))
    person.tekun_type = safe_str(row.get("供养类型", person.tekun_type))
    person.jisheng = safe_str(row.get("是否计生家庭", person.jisheng))
    person.social_card1 = safe_str(row.get("社保卡号1", person.social_card1))
    _card2 = safe_str(row.get("社保卡号2", "")).strip()
    if _card2:
        person.social_card2 = _card2
    _card3 = safe_str(row.get("社保卡号3", "")).strip()
    if _card3:
        person.social_card3 = _card3
    person.land_area = get_land_area_from_row_existing(row, person)
    person.local_welfare_forest_area = get_local_welfare_forest_from_row_existing(row, person)
    person.national_welfare_forest_area = get_national_welfare_forest_from_row_existing(row, person)
    person.commercial_forest_area = get_commercial_forest_from_row_existing(row, person)
