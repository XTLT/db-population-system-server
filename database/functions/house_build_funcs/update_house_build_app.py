"""更新一条建房申请：按传入字段部分更新，传了 members 就整体重建成员。"""

from datetime import datetime
from uuid import uuid4

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp, HouseBuildMember
from .create_house_build_app import normalize_approvals
from .fields import APP_FIELDS, to_number
from .serialize_app import serialize_app
from .signature import normalize_signature


def update_house_build_app(app_id, data, operator=''):
    data = data or {}
    session = get_session()
    try:
        app = session.get(HouseBuildApp, app_id)
        if app is None:
            return None

        for field in APP_FIELDS:
            if field in ('applicant_signature', 'applicant_signature_at'):
                continue
            if field in data and data.get(field) is not None:
                setattr(app, field, str(data.get(field)).strip())
        if 'applicant_signature' in data and data.get('applicant_signature') is not None:
            signature = normalize_signature(data.get('applicant_signature'))
            app.applicant_signature = signature
            signature_at = str(data.get('applicant_signature_at') or '').strip()
            app.applicant_signature_at = signature_at if signature else ''
            if signature and not app.applicant_signature_at:
                app.applicant_signature_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'person_id' in data and data.get('person_id') is not None:
            app.person_id = str(data.get('person_id')).strip()

        app.owner_name = (app.owner_name or '').strip()
        if not app.owner_name:
            raise ValueError('申请人姓名不能为空')

        app.apply_area_num = to_number(app.apply_land_area)
        app.approval_area_num = to_number(app.approval_land_area)
        if 'approvals' in data:
            app.approvals_json = normalize_approvals(data.get('approvals'))
        app.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        app.updated_by = operator or ''

        members = None
        if 'members' in data:
            session.query(HouseBuildMember).filter(
                HouseBuildMember.app_id == app_id
            ).delete(synchronize_session=False)
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

        session.commit()
        if members is None:
            members = (
                session.query(HouseBuildMember)
                .filter(HouseBuildMember.app_id == app_id)
                .order_by(HouseBuildMember.seq)
                .all()
            )
        return serialize_app(app, members)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
