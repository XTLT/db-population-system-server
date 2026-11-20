"""导入地力补贴数据（只导入身份证号在数据库中存在的人员）。"""

import secrets
from datetime import datetime

from database import get_session, Person, LandSubsidy
from utils import safe_str
from .._read_excel_robust import _read_excel_robust
from .._backfill_social_card import _backfill_social_card
from .resolve_columns import resolve_columns
from .row_value import row_value


def import_land_subsidy_excel(file_path: str, subsidy_year: str = "",
                              progress_callback=None, dry_run: bool = False) -> dict:
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    columns = list(df.columns)
    col = resolve_columns(columns)

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
                name = row_value(row, name_col)
                if not name:
                    skipped += 1
                    errors.append(f"行{idx + 2}: 姓名为空，已跳过")
                    continue

                id_card = row_value(row, id_card_col)

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

                certified_area = row_value(row, certified_area_col)
                subsidy_area = row_value(row, subsidy_area_col)
                base_standard = row_value(row, base_standard_col)
                rape_area = row_value(row, rape_area_col)
                rape_amount = row_value(row, rape_amount_col)
                total_amount = row_value(row, total_amount_col)
                phone = row_value(row, col.get("phone"))
                bank_account = row_value(row, col.get("bank_account"))
                bank_name = row_value(row, col.get("bank_name"))
                land_time = row_value(row, col.get("land_time"))
                rape_standard = row_value(row, col.get("rape_standard"))

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

        if dry_run:
            session.rollback()
        else:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "updated": updated, "skipped": skipped,
            "errors": errors, "total": total, "not_found": not_found, "dry_run": dry_run}
