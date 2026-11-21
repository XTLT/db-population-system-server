"""把某位到龄人员标记为"已办理"，并立即刷新当月提醒通知。

"已办理"按（人员, 年龄档）永久生效：办过的人从此不再出现在到龄提醒里，
不受目标月份滚动影响。target_month 只记录"在哪个目标月办的"，用于追溯。
"""

from datetime import datetime

from .._base import get_session
from ..models.age_notice_handled import AgeNoticeHandled
from .ensure_age_notifications_funcs import ensure_age_notifications, parse_month


def mark_age_notice_handled(person_id, age_group=60, month=None, operator='',
                            person_name='', id_card=''):
    """幂等：同一个人同一档重复点只会有一条记录。"""
    year, target_month = parse_month(month)
    month_key = '%04d-%02d' % (year, target_month)
    record_id = '%s_%d' % (person_id, age_group)

    session = get_session()
    try:
        record = session.get(AgeNoticeHandled, record_id)
        if record is None:
            session.add(AgeNoticeHandled(
                id=record_id,
                person_id=person_id,
                person_name=person_name or '',
                id_card=id_card or '',
                age_group=age_group,
                target_month=month_key,
                handled_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                handled_by=operator or '',
            ))
        else:
            record.target_month = month_key
            if person_name:
                record.person_name = person_name
            if id_card:
                record.id_card = id_card
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    ensure_age_notifications(force=True)
    return True
