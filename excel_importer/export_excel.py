import pandas as pd
from database import get_session, Person
from config import EXCEL_TEMPLATE_COLUMNS
from excel_area_fields import (
    get_land_area_export_value,
    get_local_welfare_forest_export_value,
    get_national_welfare_forest_export_value,
    get_commercial_forest_export_value,
)
from .query_persons_with_filters import query_persons_with_filters


def export_excel(file_path: str, progress_callback=None, filters: dict = None) -> bool:
    if filters:
        persons = query_persons_with_filters(filters)
    else:
        session = get_session()
        try:
            persons = session.query(Person).all()
        finally:
            session.close()

    if not persons:
        return False

    data = []
    for i, p in enumerate(persons):
        data.append({
            "户号": p.hu_hao,
            "身份证号": p.id_card,
            "姓名": p.name,
            "地址": p.address,
            "与户主关系": p.relation,
            "是否死亡": p.is_dead,
            "电话": p.phone,
            "备注": p.remark,
            "脱贫户或监测户": p.poor_type,
            "残疾": p.disability,
            "残疾等级": p.dis_level,
            "低保": p.dibao,
            "特困供养": p.tekun,
            "供养类型": p.tekun_type,
            "是否计生家庭": p.jisheng,
            "社保卡号1": p.social_card1,
            "社保卡号2": (p.social_card2 or "") + (f"（{p.social_card2_source}）" if p.social_card2 and p.social_card2_source else ""),
            "社保卡号3": (p.social_card3 or "") + (f"（{p.social_card3_source}）" if p.social_card3 and p.social_card3_source else ""),
            "土地面积": get_land_area_export_value(p),
            "地方公益林": get_local_welfare_forest_export_value(p),
            "国家公益林": get_national_welfare_forest_export_value(p),
            "非国有天然商品林": get_commercial_forest_export_value(p),
        })
        if progress_callback and (i + 1) % 100 == 0:
            progress_callback(int((i + 1) / len(persons) * 100))
    df = pd.DataFrame(data, columns=EXCEL_TEMPLATE_COLUMNS)
    df.to_excel(file_path, index=False, engine="openpyxl")
    return True
