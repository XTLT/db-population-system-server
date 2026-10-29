from database import get_session, Person
from utils import calculate_age
from excel_area_fields import (
    apply_land_area_filter,
    apply_local_welfare_forest_filter,
    apply_national_welfare_forest_filter,
    apply_commercial_forest_filter,
)


def query_persons_with_filters(filters: dict) -> list:
    session = get_session()
    try:
        query = session.query(Person)

        if filters.get("name"):
            query = query.filter(Person.name.contains(filters["name"]))
        if filters.get("address"):
            query = query.filter(Person.address.contains(filters["address"]))
        if filters.get("is_dead") and filters["is_dead"] != "全部":
            query = query.filter(Person.is_dead == filters["is_dead"])
        relation = filters.get("relation", [])
        if relation:
            query = query.filter(Person.relation.in_(relation))
        disability = filters.get("disability", [])
        if disability:
            query = query.filter(Person.disability.in_(disability))
        if filters.get("dis_level"):
            dis_level = filters["dis_level"]
            if isinstance(dis_level, list) and dis_level:
                query = query.filter(Person.dis_level.in_(dis_level))
            elif isinstance(dis_level, str) and dis_level != "全部":
                query = query.filter(Person.dis_level == dis_level)
        poor_type = filters.get("poor_type", [])
        if poor_type:
            # 脱贫类型按户号命中（与统计口径一致）：
            # 户内任一在世成员是该类型 → 该户命中；"一般户" = 户内无任何在世成员有脱贫类型
            hh_ok = (Person.hu_hao != '') & (Person.hu_hao.isnot(None))
            alive = (Person.is_dead != '是') | (Person.is_dead.is_(None))
            if poor_type == ['一般户']:
                typed = session.query(Person.hu_hao).filter(
                    hh_ok, alive,
                    Person.poor_type != '', Person.poor_type.isnot(None)
                ).distinct()
                query = query.filter(hh_ok, ~Person.hu_hao.in_(typed))
            elif '一般户' in poor_type:
                others = [t for t in poor_type if t != '一般户']
                hit = session.query(Person.hu_hao).filter(
                    hh_ok, alive, Person.poor_type.in_(others)
                ).distinct()
                typed = session.query(Person.hu_hao).filter(
                    hh_ok, alive,
                    Person.poor_type != '', Person.poor_type.isnot(None)
                ).distinct()
                query = query.filter(hh_ok, Person.hu_hao.in_(hit) | ~Person.hu_hao.in_(typed))
            else:
                hit = session.query(Person.hu_hao).filter(
                    hh_ok, alive, Person.poor_type.in_(poor_type)
                ).distinct()
                query = query.filter(hh_ok, Person.hu_hao.in_(hit))
        if filters.get("dibao") and filters["dibao"] != "全部":
            query = query.filter(Person.dibao == filters["dibao"])
        if filters.get("tekun") and filters["tekun"] != "全部":
            query = query.filter(Person.tekun == filters["tekun"])
        if filters.get("jisheng") and filters["jisheng"] != "全部":
            query = query.filter(Person.jisheng == filters["jisheng"])
        land = filters.get("land_area", "全部")
        query = apply_land_area_filter(query, land, Person)
        local_welfare_forest = filters.get("local_welfare_forest_area", "全部")
        query = apply_local_welfare_forest_filter(query, local_welfare_forest, Person)
        national_welfare_forest = filters.get("national_welfare_forest_area", "全部")
        query = apply_national_welfare_forest_filter(query, national_welfare_forest, Person)
        commercial_forest = filters.get("commercial_forest_area", "全部")
        query = apply_commercial_forest_filter(query, commercial_forest, Person)

        persons = query.all()

        if filters.get("age_min") or filters.get("age_max"):
            age_min = int(filters["age_min"]) if filters.get("age_min") else 0
            age_max = int(filters["age_max"]) if filters.get("age_max") else 999
            filtered = []
            for p in persons:
                age = -1
                if p.age:
                    try:
                        age = int(p.age)
                    except (ValueError, TypeError):
                        pass
                if age < 0 and p.id_card:
                    age_str = calculate_age(p.id_card)
                    if age_str:
                        try:
                            age = int(age_str)
                        except (ValueError, TypeError):
                            pass
                if age >= 0 and age_min <= age <= age_max:
                    filtered.append(p)
            persons = filtered

        return persons
    finally:
        session.close()
