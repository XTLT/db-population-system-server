"""生成申请编号：HB-<年份>-<4 位流水>，按当年已有记录最大流水递增。"""

from datetime import datetime

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp


def gen_app_id(prefix='HB', year=None):
    year = year or datetime.now().year
    head = '%s-%d-' % (prefix, year)
    session = get_session()
    try:
        rows = (
            session.query(HouseBuildApp.app_no)
            .filter(HouseBuildApp.app_no.like(head + '%'))
            .all()
        )
    finally:
        session.close()

    max_seq = 0
    for (no,) in rows:
        tail = (no or '')[len(head):]
        if tail.isdigit():
            max_seq = max(max_seq, int(tail))
    return '%s%04d' % (head, max_seq + 1)
