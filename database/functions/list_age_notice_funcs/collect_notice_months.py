"""从已生成的到龄提醒通知里取出目标月份（YYYYMM 整数），用来确定累积名单的起点。

提醒 id 形如 `notif_age60_202612`，后缀就是该期名单的目标月。
只要某期通知还在，那一期出现过的人就该继续留在待办名单里（未办理的人不随月份滚动消失）。
"""

from ...models.notification import Notification


def collect_notice_months(session, age):
    prefix = "notif_age%d_" % age
    months = []
    for nid, in (
        session.query(Notification.id)
        .filter(Notification.id.like(prefix + "%"))
        .all()
    ):
        try:
            months.append(int(nid[len(prefix):]))
        except (ValueError, TypeError):
            continue
    return months
