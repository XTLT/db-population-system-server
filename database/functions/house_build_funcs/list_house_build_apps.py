"""分页查询建房申请列表，可带关键字/状态/年份/小组过滤，并返回面积合计。"""

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp, HouseBuildMember
from .serialize_app import serialize_app


def list_house_build_apps(keyword='', status='', year=None, group_name='',
                          page=1, page_size=20):
    session = get_session()
    try:
        query = session.query(HouseBuildApp)
        keyword = (keyword or '').strip()
        if keyword:
            like = '%' + keyword + '%'
            query = query.filter(
                (HouseBuildApp.owner_name.like(like))
                | (HouseBuildApp.owner_id_card.like(like))
                | (HouseBuildApp.hu_hao.like(like))
                | (HouseBuildApp.app_no.like(like))
                | (HouseBuildApp.owner_phone.like(like))
            )
        if status:
            query = query.filter(HouseBuildApp.status == status)
        if group_name:
            query = query.filter(HouseBuildApp.group_name == group_name)
        if year:
            query = query.filter(HouseBuildApp.created_at.like('%s%%' % str(year)))

        total = query.count()
        sum_area = 0.0
        for (value,) in query.with_entities(HouseBuildApp.apply_area_num).all():
            sum_area += float(value or 0)

        try:
            page = max(1, int(page))
            page_size = max(1, min(200, int(page_size)))
        except (TypeError, ValueError):
            page, page_size = 1, 20

        rows = (
            query.order_by(HouseBuildApp.created_at.desc(), HouseBuildApp.app_no.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        app_ids = [row.id for row in rows]
        member_map = {}
        if app_ids:
            members = (
                session.query(HouseBuildMember)
                .filter(HouseBuildMember.app_id.in_(app_ids))
                .order_by(HouseBuildMember.app_id, HouseBuildMember.seq)
                .all()
            )
            for m in members:
                member_map.setdefault(m.app_id, []).append(m)

        items = [serialize_app(row, member_map.get(row.id, [])) for row in rows]
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 0,
            'sum_apply_area': round(sum_area, 2),
            'items': items,
        }
    finally:
        session.close()
