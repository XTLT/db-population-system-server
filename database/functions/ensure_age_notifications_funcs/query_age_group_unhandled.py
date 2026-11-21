"""查出下月到龄、且还没标记"已办理"的人员。"""

from ...models.age_notice_handled import AgeNoticeHandled
from .query_age_group import query_age_group


def query_age_group_unhandled(session, age, target_year, target_month):
    persons = query_age_group(session, age, target_year, target_month)
    if not persons:
        return []

    month_key = "%04d-%02d" % (target_year, target_month)
    handled = {
        row.person_id
        for row in session.query(AgeNoticeHandled)
        .filter(
            AgeNoticeHandled.age_group == age,
            AgeNoticeHandled.target_month == month_key,
        )
        .all()
    }
    if not handled:
        return persons
    return [p for p in persons if p.id not in handled]
