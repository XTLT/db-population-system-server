import secrets
from datetime import datetime
from database import get_session, Person, LandSubsidy
from utils import safe_str
from ._read_excel_robust import _read_excel_robust
from ._backfill_social_card import _backfill_social_card


# 地力补贴列名别名兼容表：逻辑字段 -> 可能出现的列名（按优先级从高到低）
# 同时兼容模板长名（excel_payment_templates/_constants.py）与历史短名。
LAND_SUBSIDY_COLUMN_ALIASES = {
    "name": ["姓名", "户主姓名", "承包人姓名"],
    "id_card": ["身份证号", "身份证号码", "公民身份证号码"],
    "phone": ["电话号码", "电话"],
    "bank_account": ["银行账号", "银行卡号", "打款账号"],
    "bank_name": ["金融机构", "开户行", "银行机构"],
    # 确权颁证面积（模板）/ 确权面积 / 耕地面积 / 土地面积（历史短名）
    "certified_area": ["确权颁证面积", "确权面积", "耕地面积", "土地面积"],
    # 补贴面积（亩）（模板）/ 补贴面积（历史短名）
    "subsidy_area": ["补贴面积（亩）", "补贴面积"],
    # 基础补贴标准（元/亩）（模板）/ 补贴标准 / 基础标准 / 耕地标准（新模板）
    "base_standard": ["基础补贴标准（元/亩）", "基础补贴标准", "补贴标准", "基础标准", "耕地标准"],
    # 其中种植油菜面积（模板）/ 油菜面积（历史短名）
    "rape_area": ["其中种植油菜面积", "油菜面积"],
    # 油菜标准
    "rape_standard": ["油菜标准"],
    # 其中种植油菜金额（模板）/ 油菜金额（历史短名）
    "rape_amount": ["其中种植油菜金额", "油菜金额"],
    # 补贴总金额（元）（模板）/ 补贴总金额 / 总金额 / 补贴金额 / 合计金额 / 发放金额（新模板）
    "total_amount": ["补贴总金额（元）", "补贴总金额", "总金额", "补贴金额", "合计金额", "发放金额"],
    "land_time": ["上账时间", "到账时间", "发放时间"],
}


def _resolve_columns(columns, aliases=LAND_SUBSIDY_COLUMN_ALIASES):
    """根据别名表在实际列名中定位每个逻辑字段对应的列名。

    返回 dict: 逻辑字段 -> 实际列名（未命中为 None）。
    同名别名只解析一次，避免不同逻辑字段争抢同一列。
    """
    resolved = {}
    used = set()
    for field, names in aliases.items():
        for n in names:
            if n in columns and n not in used:
                resolved[field] = n
                used.add(n)
                break
        else:
            resolved[field] = None
    return resolved


def _row_value(row, col):
    return safe_str(row.get(col, "")) if col else ""


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

    # 统一通过别名表解析列名（模板长名 + 历史短名都认）
    col = _resolve_columns(columns)

    name_col = col["name"]
    id_card_col = col["id_card"]
    certified_area_col = col["certified_area"]
    subsidy_area_col = col["subsidy_area"]
    base_standard_col = col["base_standard"]
    rape_area_col = col["rape_area"]
    rape_amount_col = col["rape_amount"]
    total_amount_col = col["total_amount"]

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    total = len(df)
    imported = 0
    updated = 0
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

    # 同年同人去重：已存在该年度记录则覆盖更新（地力补贴一年一导入，不应重复）
    existing_by_key = {}
    try:
        if subsidy_year:
            for r in session.query(LandSubsidy).filter(LandSubsidy.year == subsidy_year).all():
                if r.id_card:
                    existing_by_key[(r.id_card, r.year)] = r
    except Exception:
        pass

    try:
        for idx, row in df.iterrows():
            try:
                name = _row_value(row, name_col)
                if not name:
                    skipped += 1
                    errors.append(f"行{idx + 2}: 姓名为空，已跳过")
                    continue

                id_card = _row_value(row, id_card_col)

                # 检查身份证号是否在数据库中存在
                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    errors.append(f"行{idx + 2}: {name}({id_card}) 未在人员库中找到，已跳过")
                    skipped += 1
                    continue

                # 方案C：社保卡2/3 自动回填（期数为空则跳过回填）
                card = safe_str(row.get("卡号", "")).strip()
                person = person_map.get(id_card)
                if person and card and subsidy_year:
                    _backfill_social_card(person, f"地力补贴{subsidy_year}", card)

                certified_area = _row_value(row, certified_area_col)
                subsidy_area = _row_value(row, subsidy_area_col)
                base_standard = _row_value(row, base_standard_col)
                rape_area = _row_value(row, rape_area_col)
                rape_amount = _row_value(row, rape_amount_col)
                total_amount = _row_value(row, total_amount_col)
                phone = _row_value(row, col.get("phone"))
                bank_account = _row_value(row, col.get("bank_account"))
                bank_name = _row_value(row, col.get("bank_name"))
                land_time = _row_value(row, col.get("land_time"))
                rape_standard = _row_value(row, col.get("rape_standard"))

                # 兼容历史：土地面积/补贴金额兜底
                land_area = certified_area
                subsidy_amount = total_amount

                existing = existing_by_key.get((id_card, subsidy_year))
                if existing is not None:
                    # 同年同人已存在：覆盖更新，避免重复记录
                    existing.name = name
                    existing.id_card = id_card
                    existing.year = subsidy_year
                    existing.land_area = land_area
                    existing.subsidy_amount = subsidy_amount
                    existing.certified_area = certified_area
                    existing.subsidy_area = subsidy_area
                    existing.base_standard = base_standard
                    existing.rape_area = rape_area
                    existing.rape_amount = rape_amount
                    existing.total_amount = total_amount
                    existing.phone = phone
                    existing.bank_account = bank_account
                    existing.bank_name = bank_name
                    existing.land_time = land_time
                    existing.rape_standard = rape_standard
                    updated += 1
                else:
                    subsidy = LandSubsidy(
                        id=f"ls_{secrets.token_hex(8)}",
                        name=name,
                        id_card=id_card,
                        year=subsidy_year,
                        land_area=land_area,
                        subsidy_amount=subsidy_amount,
                        certified_area=certified_area,
                        subsidy_area=subsidy_area,
                        base_standard=base_standard,
                        rape_area=rape_area,
                        rape_amount=rape_amount,
                        total_amount=total_amount,
                        phone=phone,
                        bank_account=bank_account,
                        bank_name=bank_name,
                        land_time=land_time,
                        rape_standard=rape_standard,
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

    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}
