import os
import secrets
from datetime import datetime
from database import get_session, Person, DisabilityCarePayment
from utils import safe_str
from ._read_excel_robust import _read_excel_robust
from ._backfill_social_card import _backfill_social_card


def import_disability_care_payment_excel(file_path: str, progress_callback=None, period: str = "", import_source: str = "") -> dict:
    """导入残疾人护理补贴数据

    支持两种Excel格式：
    1. 低保特困发放台账：包含救助类型列，只导入救助类型包含'残疾人护理补贴相关关键字'的记录
    2. 通用格式：包含姓名/人员姓名、身份证号、金额/家庭保障总金额

    只导入身份证号在数据库中存在的人员
    period: 用户指定的费款所属期，Excel中无费款所属期列时使用
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    columns = list(df.columns)
    file_name = import_source or os.path.basename(file_path)

    has_subsidy_type = "救助类型" in columns and "人员身份证号" in columns

    name_col = None
    id_card_col = None
    amount_col = None

    if has_subsidy_type:
        name_col = "人员姓名" if "人员姓名" in columns else "姓名"
        id_card_col = "人员身份证号"
        amount_col = "家庭保障总金额"
    elif "姓名" in columns:
        name_col = "姓名"
        if "公民身份证号码" in columns:
            id_card_col = "公民身份证号码"
        elif "身份证号" in columns:
            id_card_col = "身份证号"
        elif "身份证号码" in columns:
            id_card_col = "身份证号码"
        amount_col = "金额" if "金额" in columns else None

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

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
                    errors.append(f"行{idx + 2}: 姓名为空，已跳过")
                    continue

                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""

                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    errors.append(f"行{idx + 2}: {name}({id_card}) 未在人员库中找到，已跳过")
                    skipped += 1
                    continue

                # 方案C：社保卡2/3 自动回填（期数为空则跳过回填）
                card = safe_str(row.get("卡号", "")).strip()
                period_value = safe_str(row.get("费款所属期", "")) or period
                person = person_map.get(id_card)
                if person and card and period_value:
                    _backfill_social_card(person, f"残疾人护理补贴{period_value}", card)

                amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                record = DisabilityCarePayment(
                    id=f"dcp_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=safe_str(row.get("所属乡镇", "")),
                    village=safe_str(row.get("所属村", "")),
                    period=safe_str(row.get("费款所属期", "")) or period,
                    payment_status=safe_str(row.get("支付标志", "")),
                    personal_code=safe_str(row.get("个人编号", "")),
                    bank_account=safe_str(row.get("银行账号", "")),
                    amount=amount,
                    relation=safe_str(row.get("和申请人关系", "")),
                    fail_reason=safe_str(row.get("失败原因", "")),
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(record)
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
