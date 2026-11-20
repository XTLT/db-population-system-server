"""确保"下月满 60 周岁 / 满 80 周岁"两条提醒通知已存在。"""

import time

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ...models.notification import Notification
from ..._base import get_session
from .age_notification_cache import (
    checked_months, checked_lock, CACHE_TTL, CACHE_FOREVER,
)
from .next_month import next_month
from .query_age_group import query_age_group
from .format_age_content import format_age_content


def ensure_age_notifications(today=None):
    target_year, target_month = next_month(today)
    key = (target_year, target_month)
    now = time.monotonic()
    with checked_lock:
        last = checked_months.get(key)
        if last is not None and now - last < CACHE_TTL:
            return

    session = get_session()
    try:
        created = 0
        missing = 0
        for age in (60, 80):
            nid = "notif_age%d_%d%02d" % (age, target_year, target_month)
            if session.get(Notification, nid) is not None:
                continue
            persons = query_age_group(session, age, target_year, target_month)
            if not persons:
                missing += 1
                continue
            session.add(Notification(
                id=nid,
                title="%d 月到龄提醒：满 %d 周岁（%d 人）" % (target_month, age, len(persons)),
                content=format_age_content(persons),
                notification_type="business",
                target_user="",
                sender_id="system",
                sender_name="系统",
                is_read="否",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                read_at="",
            ))
            created += 1
        if created:
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
        with checked_lock:
            checked_months[key] = CACHE_FOREVER if missing == 0 else time.monotonic()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
