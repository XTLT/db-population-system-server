"""读该档位的"已办理"记录，分成两类。

- 更早月份办的：从名单里去掉（"办理后的下一个月才消失"）。
- 本月办的：仍然留在名单里，标成已办理，下个月起才消失。
"""

from ...models.age_notice_handled import AgeNoticeHandled


def load_handled(session, age, current_ym):
    """current_ym 是当前自然月 "YYYY-MM"。"""
    hidden, handled_this_month = set(), set()
    for row in (
        session.query(AgeNoticeHandled)
        .filter(AgeNoticeHandled.age_group == age)
        .all()
    ):
        handled_ym = (row.handled_at or "")[:7]
        if handled_ym and handled_ym >= current_ym:
            handled_this_month.add(row.person_id)
        else:
            hidden.add(row.person_id)
    return hidden, handled_this_month
