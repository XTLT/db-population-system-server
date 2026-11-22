"""离线全量包：一次查询聚合所有人的补贴发放记录。

与 `/api/person/<id>/subsidies` 保持同一响应结构，避免移动端离线详情
再为每个人单独请求。只返回有补贴记录的人员，没有记录的人员由调用方
按空结构处理。
"""

from collections import defaultdict

from ..person_detail_funcs.subsidy_modules import MAX_RECORDS, SUBSIDY_MODULES
from ..person_detail_funcs.to_amount import to_amount


def build_subsidies_for_all(session, person_names):
    records_by_person = defaultdict(list)
    counts_by_person = defaultdict(lambda: defaultdict(int))
    totals_by_person = defaultdict(lambda: defaultdict(float))

    for module, label, model, period_attr, amount_attr in SUBSIDY_MODULES:
        rows = session.query(model).all()
        for row in rows:
            id_card = (getattr(row, "id_card", "") or "").strip()
            if not id_card:
                continue
            period = getattr(row, period_attr, "") or ""
            amount = getattr(row, amount_attr, "") or ""
            records_by_person[id_card].append({
                "module": module,
                "label": label,
                "period": period,
                "amount": amount,
                "payment_status": getattr(row, "payment_status", "") or "",
                "fail_reason": getattr(row, "fail_reason", "") or "",
                "village": getattr(row, "village", "") or "",
                "town": getattr(row, "town", "") or "",
                "bank_account": getattr(row, "bank_account", "") or "",
            })
            counts_by_person[id_card][module] += 1
            totals_by_person[id_card][module] += to_amount(amount)

    result = {}
    for id_card, records in records_by_person.items():
        records.sort(key=lambda item: (item["period"] or ""), reverse=True)
        total_records = len(records)
        by_module = []
        for module, label, _model, _period_attr, _amount_attr in SUBSIDY_MODULES:
            count = counts_by_person[id_card].get(module, 0)
            if count <= 0:
                continue
            total = totals_by_person[id_card].get(module, 0.0)
            by_module.append({
                "module": module,
                "label": label,
                "count": count,
                "total_amount": f"{total:.2f}" if total else "",
            })
        result[id_card] = {
            "id_card": id_card,
            "person_name": person_names.get(id_card, ""),
            "total_count": total_records,
            "truncated": total_records > MAX_RECORDS,
            "by_module": by_module,
            "records": records[:MAX_RECORDS],
        }
    return result
