"""ensure_age_notifications 函数：生成"下月到龄（60/80 周岁）"提醒通知。

设计要点：
- 懒生成：每次拉通知列表时调用一次，不需要 systemd timer，不会漏月；
- 幂等：通知 id 固定为 notif_age{年龄}_{目标年}{目标月}，已存在则跳过；
- 口径：按身份证第 7-14 位（YYYYMMDD）算，出生月落在下个月、且下月生日当天
  满 60/80 周岁（即出生年 = 目标年 - 年龄，出生月 = 目标月，日不限，2/29 也算）；
- 排除已死亡、已迁出的人员；
- 名单为空不生成通知，避免每月多出两条空提醒。
"""

import threading
import time
from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from ..models.notification import Notification
from ..models.person import Person
from .._base import get_session

# 名单正文最多列出的条数，超出只给总数（mobile 通知正文太长不好看）
MAX_LINES = 100

# 进程内缓存：(年, 月) -> 上次检查的 monotonic 时间戳。
# 当月两组名单都已生成时记为永久（不再重扫）；只要有一组为空，就只缓存
# _CACHE_TTL 秒，让当月后续新导入的到龄人员能在下一次拉取时补进通知。
# （原先用 set 永久缓存：某个空月被检查过一次后再导入人员，就永远补不进名单。）
_checked_months = {}
_checked_lock = threading.Lock()
_CACHE_TTL = 600  # 秒
_CACHE_FOREVER = float("inf")


def _next_month(today=None):
    """返回下个月的 (年, 月)。"""
    today = today or date.today()
    if today.month == 12:
        return today.year + 1, 1
    return today.year, today.month + 1


def _alive_condition():
    return or_(Person.is_dead.is_(None), Person.is_dead != "是")


def _not_migrated_condition():
    return or_(Person.is_migrated.is_(None), Person.is_migrated != "是")


def _query_group(session, age, target_year, target_month):
    """查出下月过生日、届时满 age 周岁的人员。"""
    birth_year = str(target_year - age)
    birth_month = "%02d" % target_month
    return (
        session.query(Person)
        .filter(
            func.length(Person.id_card) == 18,
            func.substr(Person.id_card, 7, 4) == birth_year,
            func.substr(Person.id_card, 11, 2) == birth_month,
            _alive_condition(),
            _not_migrated_condition(),
        )
        .order_by(Person.address, Person.group_name, Person.name)
        .all()
    )


def _format_content(persons):
    """把人员列表排成便于照着办手续的正文。"""
    lines = []
    for idx, p in enumerate(persons[:MAX_LINES], 1):
        id_card = p.id_card or ""
        birthday = ""
        if len(id_card) >= 14:
            birthday = "%s-%s-%s" % (id_card[6:10], id_card[10:12], id_card[12:14])
        where = " ".join(x for x in (p.group_name, p.address) if x)
        phone = ("  电话 %s" % p.phone) if p.phone else ""
        lines.append("%d. %s  %s  %s  生日 %s%s" % (idx, p.name or "", id_card, where, birthday, phone))
    if len(persons) > MAX_LINES:
        lines.append("…… 共 %d 人，此处只列前 %d 条，完整名单请按生日到人员查询里筛" % (len(persons), MAX_LINES))
    return "\n".join(lines)


def ensure_age_notifications(today=None):
    """确保"下月满 60 周岁 / 满 80 周岁"两条提醒通知已存在。

    重复调用安全；当月名单已完整生成后不再重复扫描。
    """
    target_year, target_month = _next_month(today)
    key = (target_year, target_month)
    now = time.monotonic()
    with _checked_lock:
        last = _checked_months.get(key)
        if last is not None and now - last < _CACHE_TTL:
            return

    session = get_session()
    try:
        created = 0
        missing = 0
        for age in (60, 80):
            nid = "notif_age%d_%d%02d" % (age, target_year, target_month)
            if session.get(Notification, nid) is not None:
                continue
            persons = _query_group(session, age, target_year, target_month)
            if not persons:
                missing += 1
                continue
            session.add(Notification(
                id=nid,
                title="%d 月到龄提醒：满 %d 周岁（%d 人）" % (target_month, age, len(persons)),
                content=_format_content(persons),
                notification_type="business",
                target_user="",  # 空 = 全员可见
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
                # 另一个 worker 抢先写入了同一个 id：结果等同"已生成"，不算失败
                session.rollback()
        with _checked_lock:
            _checked_months[key] = _CACHE_FOREVER if missing == 0 else time.monotonic()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
