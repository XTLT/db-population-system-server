"""待核销清单的补贴模块汇总与「已核销」快照签名。

核销时把当时"这人挂着哪几类补贴、各几笔、合计多少钱"压成一个签名字符串存下来。
之后清单再算一遍签名：和存的一致说明没变化（继续保持已核销）；不一致说明
补发/新增了补贴，这时该人重新回到清单，提醒再处理。
"""

from .subsidy_modules import SUBSIDY_MODULES
from .to_amount import to_amount


def collect_modules(session, id_cards):
    """一次 in_() 汇总六张补贴表 -> {id_card: {module: info}}。"""
    cards = [c for c in (id_cards or []) if c]
    agg = {}
    if not cards:
        return agg

    for module, label, model, period_attr, amount_attr in SUBSIDY_MODULES:
        rows = (
            session.query(model)
            .filter(getattr(model, 'id_card').in_(cards))
            .all()
        )
        for r in rows:
            card = (getattr(r, 'id_card', '') or '').strip()
            if not card:
                continue
            slot = agg.setdefault(card, {})
            period = (getattr(r, period_attr, '') or '').strip()
            amount = (getattr(r, amount_attr, '') or '').strip()
            info = slot.get(module)
            if info is None:
                info = {
                    'module': module,
                    'label': label,
                    'count': 0,
                    'total_amount_value': 0.0,
                    'latest_period': period,
                    'last_amount': amount,
                }
                slot[module] = info
            info['count'] += 1
            info['total_amount_value'] += to_amount(amount)
            if period and (not info['latest_period'] or period > info['latest_period']):
                info['latest_period'] = period
                info['last_amount'] = amount

    return agg


def build_module_list(mods):
    """{module: info} -> 按模块名排序的展示列表。"""
    out = []
    for m in sorted((mods or {}).values(), key=lambda x: x['label']):
        total = m['total_amount_value']
        out.append({
            'module': m['module'],
            'label': m['label'],
            'count': m['count'],
            'total_amount': f"{total:.2f}" if total else '',
            'latest_period': m['latest_period'],
            'last_amount': m['last_amount'],
        })
    return out


def sign_module_list(module_list):
    """签名：模块键:笔数:合计金额，按模块键排序拼接。"""
    parts = []
    for m in sorted(module_list or [], key=lambda x: x.get('module', '')):
        parts.append('%s:%s:%s' % (
            m.get('module', ''), m.get('count', 0), m.get('total_amount', '')))
    return ','.join(parts)


def signature_for_person(session, id_card):
    """返回（签名, 模块展示列表）；名下已无补贴时签名为空串。"""
    card = (id_card or '').strip()
    if not card:
        return '', []
    mods = collect_modules(session, [card]).get(card) or {}
    module_list = build_module_list(mods)
    return sign_module_list(module_list), module_list
