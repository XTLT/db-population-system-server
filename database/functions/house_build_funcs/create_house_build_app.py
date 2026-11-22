"""新建一条宅基地建房申请（申请表 + 审批表字段一次落库，家庭成员另表存）。"""

import json
from datetime import datetime
from uuid import uuid4

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp, HouseBuildMember
from .fields import APP_FIELDS, APPROVAL_KEYS, to_number
from .gen_app_id import gen_app_id
from .serialize_app import serialize_app
from .signature import normalize_signature


def _clean(data, key):
    v = data.get(key)
    if v is None:
        return ''
    return str(v).strip()


def normalize_approvals(raw):
    """把前端传来的 approvals 规整成五组 {opinion, leader, date} 的 JSON 文本。"""
    data = raw if isinstance(raw, dict) else {}
    out = {}
    for key in APPROVAL_KEYS:
        item = data.get(key) or {}
        out[key] = {
            'opinion': str(item.get('opinion') or '').strip(),
            'leader': str(item.get('leader') or '').strip(),
            'date': str(item.get('date') or '').strip(),
        }
    return json.dumps(out, ensure_ascii=False)


def create_house_build_app(data, operator=''):
    data = data or {}
    name = _clean(data, 'owner_name')
    if not name:
        raise ValueError('申请人姓名不能为空')

    app_no = _clean(data, 'app_no')
    if not app_no:
        app_no = gen_app_id()

    session = get_session()
    try:
        app_id = 'hb_' + uuid4().hex[:16]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        app = HouseBuildApp(
            id=app_id,
            app_no=app_no,
            owner_name=name,
            created_at=now,
            updated_at=now,
            created_by=operator or '',
            updated_by=operator or '',
        )
        for field in APP_FIELDS:
            if field == 'owner_name':
                continue
            if field in ('applicant_signature', 'applicant_signature_at'):
                continue
            if field in data:
                setattr(app, field, _clean(data, field))
        if 'applicant_signature' in data:
            signature = normalize_signature(data.get('applicant_signature'))
            app.applicant_signature = signature
            signature_at = _clean(data, 'applicant_signature_at')
            app.applicant_signature_at = signature_at if signature else ''
            if signature and not app.applicant_signature_at:
                app.applicant_signature_at = now
        app.person_id = _clean(data, 'person_id')
        app.apply_area_num = to_number(app.apply_land_area)
        app.approval_area_num = to_number(app.approval_land_area)
        app.approvals_json = normalize_approvals(data.get('approvals'))

        members = []
        for index, m in enumerate(data.get('members') or []):
            m = m or {}
            mem = HouseBuildMember(
                id='hbm_' + uuid4().hex[:16],
                app_id=app_id,
                seq=str(m.get('seq') or index + 1),
                name=str(m.get('name') or '').strip(),
                age=str(m.get('age') or '').strip(),
                relation=str(m.get('relation') or '').strip(),
                id_card=str(m.get('id_card') or '').strip(),
                hukou=str(m.get('hukou') or '').strip(),
            )
            if not (mem.name or mem.id_card):
                continue
            session.add(mem)
            members.append(mem)

        session.add(app)
        session.commit()
        session.refresh(app)
        result = serialize_app(app, members)
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
