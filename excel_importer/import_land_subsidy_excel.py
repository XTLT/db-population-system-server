import secrets
from datetime import datetime
from database import get_session, Person, LandSubsidy
from utils import safe_str
from ._read_excel_robust import _read_excel_robust
from ._backfill_social_card import _backfill_social_card


def import_land_subsidy_excel(file_path: str, subsidy_year: str = "", progress_callback=None) -> dict:
    """导入地力补贴数据

    只导入身份证号在数据库中存在的人员

    Args:
        file_path: Excel 文件路径
        subsidy_year: 补贴年份
        progress_callback: 进度回调函数

    Returns:
        导入结果字典
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    columns = list(df.columns)

    # 确定列名映射
    name_col = None
    id_card_col = None
    area_col = None
    amount_col = None

    if "姓名" in columns:
        name_col = "姓名"
    elif "承包人姓名" in columns:
        name_col = "承包人姓名"

    if "身份证号" in columns:
        id_card_col = "身份证号"
    elif "身份证号码" in columns:
        id_card_col = "身份证号码"
    elif "公民身份证号码" in columns:
        id_card_col = "公民身份证号码"

    if "确权面积" in columns:
        area_col = "确权面积"
    elif "耕地面积" in columns:
        area_col = "耕地面积"
    elif "土地面积" in columns:
        area_col = "土地面积"

    if "补贴金额" in columns:
        amount_col = "补贴金额"
    elif "总金额" in columns:
        amount_col = "总金额"
    elif "合计金额" in columns:
        amount_col = "合计金额"

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

    # 获取数据库中所有身份证号
    existing_id_cards = set()
    person_map = {}
    try:
        persons = session.query(Person).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
        person_map = {p.id_card: p for p in persons if p.id_card}
    except Exception:
        pass

    try:
        for idx, row in df.iterrows():
            try:
                name = safe_str(row.get(name_col, ""))
                if not name:
                    skipped += 1
                    continue

                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""

                # 检查身份证号是否在数据库中存在
                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    skipped += 1
                    continue

                # 方案C：社保卡2/3 自动回填（期数为空则跳过回填）
                card = safe_str(row.get("卡号", "")).strip()
                person = person_map.get(id_card)
                if person and card and subsidy_year:
                    _backfill_social_card(person, f"地力补贴{subsidy_year}", card)

                land_area = safe_str(row.get(area_col, "")) if area_col else ""
                subsidy_amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                # 其他可能的字段
                certified_area = safe_str(row.get("确权面积", ""))
                subsidy_area = safe_str(row.get("补贴面积", ""))
                base_standard = safe_str(row.get("补贴标准", ""))
                rape_area = safe_str(row.get("油菜面积", ""))
                rape_amount = safe_str(row.get("油菜金额", ""))
                total_amount = safe_str(row.get("总金额", ""))

                subsidy = LandSubsidy(
                    id=f"ls_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    year=subsidy_year,
                    land_area=land_area,
                    subsidy_amount=subsidy_amount or total_amount,
                    certified_area=certified_area,
                    subsidy_area=subsidy_area,
                    base_standard=base_standard,
                    rape_area=rape_area,
                    rape_amount=rape_amount,
                    total_amount=total_amount,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                session.add(subsidy)
                imported += 1

                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}
