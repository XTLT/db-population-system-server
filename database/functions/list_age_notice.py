"""到龄提醒名单（结构化返回，供逐人点"已办理"）。"""

from .._base import get_session
from .ensure_age_notifications_funcs import parse_month, query_age_group_unhandled


def _birthday(id_card):
    if len(id_card or "") >= 14:
        return "%s-%s-%s" % (id_card[6:10], id_card[10:12], id_card[12:14])
    return ""


def list_age_notice(age=None, month=None):
    """返回下月（或指定月）满 60/80 周岁、尚未办理的人员。

    已标记"已办理"的人不再出现；同一个人可能同时属于两档时按档位分别列出。
    """
    year, target_month = parse_month(month)
    ages = [age] if age in (60, 80) else [60, 80]

    session = get_session()
    try:
        groups = []
        for a in ages:
            persons = query_age_group_unhandled(session, a, year, target_month)
            groups.append({
                'age': a,
                'total': len(persons),
                'persons': [{
                    'person_id': p.id,
                    'name': p.name or '',
                    'id_card': p.id_card or '',
                    'birthday': _birthday(p.id_card),
                    'address': p.address or '',
                    'group_name': p.group_name or '',
                    'phone': p.phone or '',
                } for p in persons],
            })
        return {
            'year': year,
            'month': target_month,
            'month_label': '%d 月' % target_month,
            'month_key': '%04d-%02d' % (year, target_month),
            'total': sum(g['total'] for g in groups),
            'groups': groups,
        }
    finally:
        session.close()
