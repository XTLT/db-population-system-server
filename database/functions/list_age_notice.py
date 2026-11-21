"""到龄提醒待办名单（结构化返回，供逐人点"已办理"）。

口径（2026-11-21 与用户确认）：
- 只要某期到龄提醒出现过的人，未办理就一直留在名单里，不随月份滚动消失；
- 点"已办理"后当月仍显示（标注已办理），到下一个自然月才从名单里消失；
- "已办理"按（人员, 年龄档）记录，60 岁办过不影响 80 岁那一档的提前提醒。
"""

from datetime import date

from .._base import get_session
from .ensure_age_notifications_funcs import next_month, parse_month, query_age_group
from .list_age_notice_funcs import collect_notice_months, iter_months, load_handled


def _birthday(id_card):
    if len(id_card or "") >= 14:
        return "%s-%s-%s" % (id_card[6:10], id_card[10:12], id_card[12:14])
    return ""


def _persist_key(person, target_year, target_month):
    return (target_year * 100 + target_month, person.address or "",
            person.group_name or "", person.name or "")


def list_age_notice(age=None, month=None, today=None):
    """返回待办理的到龄人员（累积），已办理满一个自然月的人不再出现。"""
    today = today or date.today()
    if month:
        year, target_month = parse_month(month)
    else:
        year, target_month = next_month(today)
    end_ym = year * 100 + target_month
    current_ym = "%04d-%02d" % (today.year, today.month)
    ages = [age] if age in (60, 80) else [60, 80]

    session = get_session()
    try:
        groups = []
        for a in ages:
            months = collect_notice_months(session, a)
            start_ym = min(months) if months else end_ym
            if start_ym > end_ym:
                start_ym = end_ym

            hidden, handled_now = load_handled(session, a, current_ym)

            entries = []
            seen = set()
            for y, m in iter_months(start_ym, end_ym):
                for p in query_age_group(session, a, y, m):
                    if p.id in seen or p.id in hidden:
                        continue
                    seen.add(p.id)
                    entries.append((y, m, p))
            entries.sort(key=lambda item: _persist_key(item[2], item[0], item[1]))

            groups.append({
                'age': a,
                'total': len(entries),
                'handled_total': sum(1 for _, _, p in entries if p.id in handled_now),
                'persons': [{
                    'person_id': p.id,
                    'name': p.name or '',
                    'id_card': p.id_card or '',
                    'birthday': _birthday(p.id_card),
                    'address': p.address or '',
                    'group_name': p.group_name or '',
                    'phone': p.phone or '',
                    'target_month': '%04d-%02d' % (y, m),
                    'target_label': '%d 月' % m,
                    'handled': p.id in handled_now,
                } for y, m, p in entries],
            })

        return {
            'year': year,
            'month': target_month,
            'month_label': '%d 月' % target_month,
            'month_key': '%04d-%02d' % (year, target_month),
            'current_month': current_ym,
            'total': sum(g['total'] for g in groups),
            'groups': groups,
        }
    finally:
        session.close()
