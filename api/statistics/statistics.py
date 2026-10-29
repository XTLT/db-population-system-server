from flask import request, jsonify
from sqlalchemy import func

from database import get_session, Person
from utils.security import require_auth
from . import bp


@bp.route('/statistics')
@require_auth
def api_statistics():
    session = get_session()
    try:
        # 统计口径（用户确认 2026-10-29）：
        # 除"已死亡"外，所有统计均排除死亡人员（is_dead='是'）
        alive_filter = (Person.is_dead != '是') | (Person.is_dead.is_(None))

        total = session.query(Person).filter(alive_filter).count()
        dead = session.query(Person).filter(Person.is_dead == '是').count()
        migrated = session.query(Person).filter(Person.is_migrated == '是', alive_filter).count()
        # 低保人员统计：编辑页选项为 是/低保边缘家庭/特困家庭，另兼容历史旧值
        dibao = session.query(Person).filter(
            alive_filter,
            Person.dibao.in_(['是', '低保边缘家庭', '特困家庭',
                              '最低生活保障家庭', '最低生活保障边缘家庭', '单人保家庭'])
        ).count()
        disability = session.query(Person).filter(alive_filter, Person.disability != '无', Person.disability != '').count()
        # 特困供养人员统计：与编辑页选项/移动端下钻统一为 =='是'
        tekun = session.query(Person).filter(alive_filter, Person.tekun == '是').count()
        # 户数 = 有在世成员的户号去重（整户都死亡的户不计入）
        household_count = session.query(Person.hu_hao).filter(
            Person.hu_hao != '', Person.hu_hao.isnot(None),
            alive_filter
        ).distinct().count()

        poor_type_distribution = {}
        poor_type_person_count = {}

        from collections import defaultdict

        # 脱贫户/监测户按"户内任一在世成员有该类型"统计户数（每类独立计数，可重叠）
        house_types = defaultdict(set)
        for hu_hao, pt in session.query(Person.hu_hao, Person.poor_type).filter(
            Person.hu_hao != '', Person.hu_hao.isnot(None),
            alive_filter,
            Person.poor_type != '', Person.poor_type.isnot(None)
        ).all():
            house_types[hu_hao].add(pt)

        for types in house_types.values():
            for t in types:
                poor_type_distribution[t] = poor_type_distribution.get(t, 0) + 1
        # 一般户 = 总户数 - 有脱贫类型成员（在世）的户数
        poor_type_distribution['一般户'] = household_count - len(house_types)

        # 统计各 poor_type 的人数（排除死亡）
        pt_person_counts = session.query(
            Person.poor_type, func.count(Person.id)
        ).filter(
            Person.poor_type != '', Person.poor_type.isnot(None),
            alive_filter
        ).group_by(Person.poor_type).all()
        for pt_val, cnt in pt_person_counts:
            poor_type_person_count[pt_val] = cnt

        dis_level_distribution = {}
        dis_levels = session.query(Person.dis_level).filter(
            Person.dis_level != '', Person.dis_level.isnot(None), Person.dis_level != '无',
            alive_filter
        ).all()
        for dl in dis_levels:
            dl_val = dl[0] or '其他'
            dis_level_distribution[dl_val] = dis_level_distribution.get(dl_val, 0) + 1

        tekun_type_distribution = {}
        tekun_types = session.query(Person.tekun_type).filter(
            Person.tekun_type != '', Person.tekun_type.isnot(None),
            alive_filter
        ).all()
        for tt in tekun_types:
            tt_val = tt[0] or '其他'
            tekun_type_distribution[tt_val] = tekun_type_distribution.get(tt_val, 0) + 1

        land_areas = session.query(Person.land_area).filter(
            Person.land_area != '', Person.land_area.isnot(None),
            alive_filter
        ).all()
        total_land_area = 0.0
        land_count = 0
        for la in land_areas:
            try:
                area = float(la[0])
                total_land_area += area
                land_count += 1
            except (ValueError, TypeError):
                pass
        avg_land_area = round(total_land_area / land_count, 2) if land_count > 0 else 0

        local_welfare_forest_areas = session.query(Person.local_welfare_forest_area).filter(
            Person.local_welfare_forest_area != '', Person.local_welfare_forest_area.isnot(None),
            alive_filter
        ).all()
        total_local_welfare_forest_area = 0.0
        local_welfare_forest_count = 0
        for la in local_welfare_forest_areas:
            try:
                area = float(la[0])
                total_local_welfare_forest_area += area
                local_welfare_forest_count += 1
            except (ValueError, TypeError):
                pass
        avg_local_welfare_forest_area = round(total_local_welfare_forest_area / local_welfare_forest_count, 2) if local_welfare_forest_count > 0 else 0

        national_welfare_forest_areas = session.query(Person.national_welfare_forest_area).filter(
            Person.national_welfare_forest_area != '', Person.national_welfare_forest_area.isnot(None),
            alive_filter
        ).all()
        total_national_welfare_forest_area = 0.0
        national_welfare_forest_count = 0
        for la in national_welfare_forest_areas:
            try:
                area = float(la[0])
                total_national_welfare_forest_area += area
                national_welfare_forest_count += 1
            except (ValueError, TypeError):
                pass
        avg_national_welfare_forest_area = round(total_national_welfare_forest_area / national_welfare_forest_count, 2) if national_welfare_forest_count > 0 else 0

        commercial_forest_areas = session.query(Person.commercial_forest_area).filter(
            Person.commercial_forest_area != '', Person.commercial_forest_area.isnot(None),
            alive_filter
        ).all()
        total_commercial_forest_area = 0.0
        commercial_forest_count = 0
        for la in commercial_forest_areas:
            try:
                area = float(la[0])
                total_commercial_forest_area += area
                commercial_forest_count += 1
            except (ValueError, TypeError):
                pass
        avg_commercial_forest_area = round(total_commercial_forest_area / commercial_forest_count, 2) if commercial_forest_count > 0 else 0

        return jsonify({
            'total': total,
            'household_count': household_count,
            'dead': dead,
            'migrated': migrated,
            'dibao': dibao,
            'disability': disability,
            'tekun': tekun,
            'alive': total,
            'not_migrated': total - migrated,
            'poor_type_distribution': poor_type_distribution,
            'poor_type_person_count': poor_type_person_count,
            'dis_level_distribution': dis_level_distribution,
            'tekun_type_distribution': tekun_type_distribution,
            'total_land_area': round(total_land_area, 2),
            'avg_land_area': avg_land_area,
            'total_local_welfare_forest_area': round(total_local_welfare_forest_area, 2),
            'avg_local_welfare_forest_area': avg_local_welfare_forest_area,
            'total_national_welfare_forest_area': round(total_national_welfare_forest_area, 2),
            'avg_national_welfare_forest_area': avg_national_welfare_forest_area,
            'total_commercial_forest_area': round(total_commercial_forest_area, 2),
            'avg_commercial_forest_area': avg_commercial_forest_area
        })
    finally:
        session.close()
