"""把待核销清单里的某个人标记为"已核销"。

标记后该人不再出现在待核销清单（名下补贴记录本身不动，仍需人工处理）。
一个人一条记录，重复点只更新核销时的补贴快照与时间。
"""

from datetime import datetime

from .._base import get_session
from ..models.pending_correction_handled import PendingCorrectionHandled


def mark_pending_correction_handled(person_id, operator='', person_name='',
                                    id_card='', module_labels='', module_count=0,
                                    total_amount='', snapshot=''):
    if not person_id:
        raise ValueError('缺少 person_id')

    session = get_session()
    try:
        record = session.get(PendingCorrectionHandled, person_id)
        if record is None:
            record = PendingCorrectionHandled(
                id=person_id,
                person_id=person_id,
                person_name=person_name or '',
                id_card=id_card or '',
                module_labels=module_labels or '',
                module_count=module_count or 0,
                total_amount=total_amount or '',
                snapshot=snapshot or '',
                handled_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                handled_by=operator or '',
            )
            session.add(record)
        else:
            record.person_name = person_name or record.person_name
            record.id_card = id_card or record.id_card
            record.module_labels = module_labels or record.module_labels
            record.module_count = module_count or record.module_count
            record.total_amount = total_amount or record.total_amount
            record.snapshot = snapshot or ''
            record.handled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            record.handled_by = operator or record.handled_by
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return True
