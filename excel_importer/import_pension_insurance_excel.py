import os
import secrets
from datetime import datetime
from database import get_session, Person, PensionInsurance
from utils import safe_str
from ._read_excel_robust import _read_excel_robust
from ._backfill_social_card import _backfill_social_card


def import_pension_insurance_excel(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入养老保险数据

    只导入身份证号在数据库中存在的人员

    Args:
        file_path: Excel 文件路径
        progress_callback: 进度回调函数
        period: 费款所属期（如Excel中无此列则使用此值）

    Returns:
        导入结果字典
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    columns = list(df.columns)
    file_name = os.path.basename(file_path)

    # 验证必需列
    if "姓名" not in columns:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    # 确定身份证列名
    id_card_col = None
    if "公民身份证号码" in columns:
        id_card_col = "公民身份证号码"
    elif "身份证号" in columns:
        id_card_col = "身份证号"
    elif "身份证号码" in columns:
        id_card_col = "身份证号码"

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
                name = safe_str(row.get("姓名", ""))
                if not name:
                    skipped += 1
                    errors.append(f"行{idx + 2}: 姓名为空，已跳过")
                    continue

                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""

                # 检查身份证号是否在数据库中存在
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
                    _backfill_social_card(person, f"养老保险{period_value}", card)

                pension = PensionInsurance(
                    id=f"pi_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=safe_str(row.get("所属乡镇", "")),
                    village=safe_str(row.get("所属村", "")),
                    period=safe_str(row.get("费款所属期", "")) or period,
                    payment_status=safe_str(row.get("支付标志", "")),
                    personal_code=safe_str(row.get("个人编号", "")),
                    person_id=safe_str(row.get("享受定期待遇人员ID", "")),
                    bank_account=safe_str(row.get("银行账号", "")),
                    amount=safe_str(row.get("金额", "")),
                    fail_reason=safe_str(row.get("失败原因", "")),
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(pension)
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
