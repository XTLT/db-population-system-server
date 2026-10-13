from database import Person
from utils import safe_str, calculate_age
from excel_area_fields import (
    get_land_area_from_row_existing,
    get_local_welfare_forest_from_row_existing,
    get_national_welfare_forest_from_row_existing,
    get_commercial_forest_from_row_existing,
)


def _cell(row, key, default):
    """取单元格值：空值（None/空白）不覆盖已有字段，保留默认值。"""
    v = row.get(key)
    if v is None:
        return default
    s = safe_str(v)
    return default if not s.strip() else s


def _update_person_from_row(person: Person, row):
    person.hu_hao = _cell(row, "户号", person.hu_hao)
    person.name = _cell(row, "姓名", person.name)
    person.age = calculate_age(person.id_card)
    person.address = _cell(row, "地址", person.address)
    person.group_name = _cell(row, "小组", person.group_name)
    person.relation = _cell(row, "与户主关系", person.relation)
    person.is_dead = _cell(row, "是否死亡", person.is_dead)
    person.phone = _cell(row, "电话", person.phone)
    person.remark = _cell(row, "备注", person.remark)
    person.poor_type = _cell(row, "脱贫户或监测户", person.poor_type)
    person.disability = _cell(row, "残疾", person.disability)
    person.dis_level = _cell(row, "残疾等级", person.dis_level)
    person.disability_type = _cell(row, "残疾类型", person.disability_type)
    person.dibao = _cell(row, "低保", person.dibao)
    person.tekun = _cell(row, "特困供养", person.tekun)
    person.tekun_type = _cell(row, "供养类型", person.tekun_type)
    person.jisheng = _cell(row, "是否计生家庭", person.jisheng)
    person.social_card1 = _cell(row, "社保卡号1", person.social_card1)
    _card2 = _cell(row, "社保卡号2", "")
    if _card2:
        person.social_card2 = _card2
    _card3 = _cell(row, "社保卡号3", "")
    if _card3:
        person.social_card3 = _card3
    person.land_area = get_land_area_from_row_existing(row, person)
    person.local_welfare_forest_area = get_local_welfare_forest_from_row_existing(row, person)
    person.national_welfare_forest_area = get_national_welfare_forest_from_row_existing(row, person)
    person.commercial_forest_area = get_commercial_forest_from_row_existing(row, person)
