"""按 id 取一条建房申请（含成员），不存在返回 None。"""

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp, HouseBuildMember
from .serialize_app import serialize_app


def get_house_build_app(app_id):
    session = get_session()
    try:
        app = session.get(HouseBuildApp, app_id)
        if app is None:
            return None
        members = (
            session.query(HouseBuildMember)
            .filter(HouseBuildMember.app_id == app_id)
            .order_by(HouseBuildMember.seq)
            .all()
        )
        return serialize_app(app, members)
    finally:
        session.close()
