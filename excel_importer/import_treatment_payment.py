import os
import secrets
from datetime import datetime
from database import get_session, Person, TreatmentPayment
from utils import safe_str
from ._read_excel_robust import _read_excel_robust


def import_treatment_payment(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入待遇发放数据，支持三种表格格式：
    1. 待遇发放成功信息表：包含所属乡镇、所属村、费款所属期、支付标志、个人编号、公民身份证号码、姓名、银行账号、金额、失败原因
    2. 待遇支付信息表：包含所属乡镇、所属村、费款所属期、姓名、公民身份证号码、银行账号、金额、支付标志
    3. 低保特困发放台账：包含救助类型、人员姓名、人员身份证号、和申请人关系、家庭保障总金额

    只导入身份证号在数据库中存在的人员
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    # 检测表格类型
    columns = list(df.columns)
    file_name = os.path.basename(file_path)

    # 格式3：低保特困发放台账
    has_format3 = "救助类型" in columns and "人员身份证号" in columns

    # 确定姓名和身份证列名
    name_col = None
    id_card_col = None
    amount_col = None

    if has_format3:
        name_col = "人员姓名"
        id_card_col = "人员身份证号"
        amount_col = "家庭保障总金额"
    elif "姓名" in columns:
        name_col = "姓名"
        if "公民身份证号码" in columns:
            id_card_col = "公民身份证号码"
        elif "身份证号" in columns:
            id_card_col = "身份证号"
        amount_col = "金额" if "金额" in columns else None

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
    try:
        persons = session.query(Person.id_card).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
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

                amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                # 根据表格类型提取其他字段
                town = safe_str(row.get("所属乡镇", ""))
                village = safe_str(row.get("所属村", ""))
                row_period = safe_str(row.get("费款所属期", "")) or period
                payment_status = safe_str(row.get("支付标志", ""))
                personal_code = safe_str(row.get("个人编号", ""))
                bank_account = safe_str(row.get("银行账号", ""))
                fail_reason = safe_str(row.get("失败原因", ""))
                subsidy_type = safe_str(row.get("救助类型", ""))
                relation = safe_str(row.get("和申请人关系", ""))

                payment = TreatmentPayment(
                    id=f"tp_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=town,
                    village=village,
                    period=row_period,
                    payment_status=payment_status,
                    personal_code=personal_code,
                    bank_account=bank_account,
                    amount=amount,
                    subsidy_type=subsidy_type,
                    relation=relation,
                    fail_reason=fail_reason,
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(payment)
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
