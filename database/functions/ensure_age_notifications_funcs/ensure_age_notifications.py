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
from .query_age_group_unhandled import query_age_group_unhandled
from .format_age_content import format_age_content


def _fill_notification(notification, age, target_month, persons):
    notification.title = "%d 月到龄提醒：满 %d 周岁（%d 人）" % (
        target_month, age, len(persons))
    notification.content = format_age_content(persons)
    return notification


def _new_notification(nid, age, target_month, persons):
    return _fill_notification(
        Notification(
            id=nid,
            title="",
            content="",
            notification_type="business",
            target_user="",
            sender_id="system",
            sender_name="系统",
            is_read="否",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            read_at="",
        ),
        age, target_month, persons,
    )


def ensure_age_notifications(today=None, force=False):
    """生成下月到龄提醒。

    force=True 用于"已办理"之后：忽略进程内缓存，按最新名单重写已有通知；
    名单清空时把该条提醒删掉，避免通知中心还列着已办理的人。
    """
    target_year, target_month = next_month(today)
    key = (target_year, target_month)
    now = time.monotonic()

    if not force:
        with checked_lock:
            last = checked_months.get(key)
            if last is not None and now - last < CACHE_TTL:
                return

    session = get_session()
    try:
        changed = 0
        missing = 0
        for age in (60, 80):
            nid = "notif_age%d_%d%02d" % (age, target_year, target_month)
            existing = session.get(Notification, nid)
            if existing is not None and not force:
                continue

            persons = query_age_group_unhandled(session, age, target_year, target_month)
            if not persons:
                missing += 1
                if existing is not None and force:
                    session.delete(existing)
                    changed += 1
                continue

            if existing is None:
                session.add(_new_notification(nid, age, target_month, persons))
            else:
                _fill_notification(existing, age, target_month, persons)
            changed += 1

        if changed:
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
