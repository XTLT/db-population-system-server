import os
import secrets
from datetime import datetime
from database import get_session, Person, TekunPayment
from utils import safe_str
from ._read_excel_robust import _read_excel_with_header
from ._backfill_social_card import _backfill_social_card
from excel_payment_templates import TEKUN_PAYMENT_COLUMNS


def import_tekun_payment_excel(file_path: str, progress_callback=None, period: str = "", import_source: str = "") -> dict:
    """导入特困发放数据

    新模板单表头行（77列）：序号/人员编码/.../申请人姓名/申请人身份证号/城乡类型/性别/.../村名称/救助类型/...。
    保留台账过滤：救助类型不含特困则跳过；保留旧通用格式兼容。
    只导入身份证号在数据库中存在的人员。
    period: 用户指定的费款所属期，Excel中无费款所属期列时使用
    import_source: 原始上传文件名（否则回退为临时文件名 basename(file_path)）
    """

    df = _read_excel_with_header(file_path, TEKUN_PAYMENT_COLUMNS)
    df = df.fillna("")

    columns = list(df.columns)
    file_name = import_source or os.path.basename(file_path)

    def pick(*cands):
        for c in cands:
            if c in columns:
                return c
        return None

    # 台账：含救助类型列即按台账过滤（新77列模板含 救助类型 + 申请人身份证号）
    has_subsidy_type = "救助类型" in columns

    name_col = pick("申请人姓名", "人员姓名", "姓名")
    id_card_col = pick("申请人身份证号", "人员身份证号", "身份证号", "公民身份证号码", "身份证号码")
    amount_col = pick("家庭保障总金额", "金额")

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列（请使用最新模板）"], "total": 0, "not_found": []}
    if not id_card_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到身份证号列（请使用最新模板）"], "total": 0, "not_found": []}

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

                # 台账格式：过滤只导入特困记录
                if has_subsidy_type:
                    subsidy_type = safe_str(row.get("救助类型", ""))
                    if "特困" not in subsidy_type:
                        skipped += 1
                        errors.append(f"行{idx + 2}: 救助类型不含特困（{subsidy_type}），已跳过")
                        continue

                id_card = safe_str(row.get(id_card_col, ""))

                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    errors.append(f"行{idx + 2}: {name}({id_card}) 未在人员库中找到，已跳过")
                    skipped += 1
                    continue

                # 期数兜底链：费款所属期 → period 参数 → 始发年月 → 本次开始发放年月
                period_value = (safe_str(row.get("费款所属期", "")) or period
                                or safe_str(row.get("始发年月", "")) or safe_str(row.get("本次开始发放年月", "")))

                # 方案C：社保卡2/3 自动回填（期数为空则跳过回填）；卡号列若存在
                card = safe_str(row.get("卡号", "")).strip()
                person = person_map.get(id_card)
                if person and card and period_value:
                    _backfill_social_card(person, f"特困{period_value}", card)

                amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                record = TekunPayment(
                    id=f"tk_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=safe_str(row.get("镇名称", "")) or safe_str(row.get("所属乡镇", "")),
                    village=safe_str(row.get("村名称", "")) or safe_str(row.get("所属村", "")),
                    period=period_value,
                    payment_status=safe_str(row.get("支付标志", "")),
                    personal_code=safe_str(row.get("人员编码", "")) or safe_str(row.get("个人编号", "")),
                    bank_account=safe_str(row.get("银行账号", "")),
                    amount=amount,
                    relation=safe_str(row.get("和申请人关系", "")),
                    fail_reason=safe_str(row.get("失败原因", "")),
                    gender=safe_str(row.get("性别", "")),
                    family_members=safe_str(row.get("共同生活家庭成员", "")),
                    family_count=safe_str(row.get("享受保障人口数", "")),
                    base_amount=safe_str(row.get("家庭最低生活基本保障金", "")),
                    special_amount=safe_str(row.get("家庭特殊困难补助金", "")),
                    adjust_amount=safe_str(row.get("家庭调剂金额", "")),
                    special_situation=safe_str(row.get("特殊困难情形（分类施保）", "")),
                    special_subsidy=safe_str(row.get("特殊困难补助金", "")),
                    start_time=safe_str(row.get("初始享受时间", "")),
                    issue_month=safe_str(row.get("始发年月", "")),
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
