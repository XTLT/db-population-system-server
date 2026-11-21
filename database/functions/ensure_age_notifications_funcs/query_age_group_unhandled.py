"""查出下月到龄、且还没标记"已办理"的人员。

"已办理"按（人员, 年龄档）永久排除，不再随目标月份变化：
某人 60 岁办过之后，后续任何月份都不会再被提醒 60 岁这一档。
"""

from ...models.age_notice_handled import AgeNoticeHandled
from .query_age_group import query_age_group


def query_age_group_unhandled(session, age, target_year, target_month):
    persons = query_age_group(session, age, target_year, target_month)
    if not persons:
        return []

    handled = {
        row.person_id
        for row in session.query(AgeNoticeHandled)
        .filter(AgeNoticeHandled.age_group == age)
        .all()
    }
    if not handled:
        return persons
    return [p for p in persons if p.id not in handled]
