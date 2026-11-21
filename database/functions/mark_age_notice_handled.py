"""把某位到龄人员标记为"已办理"，并立即刷新当月提醒通知。"""

from datetime import datetime

from .._base import get_session
from ..models.age_notice_handled import AgeNoticeHandled
from .ensure_age_notifications_funcs import ensure_age_notifications, parse_month


def mark_age_notice_handled(person_id, age_group=60, month=None, operator='',
                            person_name='', id_card=''):
    """幂等：重复点只更新一次记录，不会产生多条。

    写入后调用 ensure_age_notifications(force=True)，让通知正文和人数同步减少；
    该档人员全部办完时，对应通知会被删除。
    """
    year, target_month = parse_month(month)
    month_key = '%04d-%02d' % (year, target_month)
    record_id = '%s_%d_%s' % (person_id, age_group, month_key)

    session = get_session()
    try:
        if session.get(AgeNoticeHandled, record_id) is None:
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
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    ensure_age_notifications(force=True)
    return True
