"""删除一条建房申请及其成员。返回是否删到东西。"""

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp, HouseBuildMember


def delete_house_build_app(app_id):
    session = get_session()
    try:
        app = session.get(HouseBuildApp, app_id)
        if app is None:
            return False
        session.query(HouseBuildMember).filter(
            HouseBuildMember.app_id == app_id
        ).delete(synchronize_session=False)
        session.delete(app)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
