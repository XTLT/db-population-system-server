def apply_land_area_filter(query, filter_value, Person):
    if filter_value == "不为0":
        return query.filter(Person.land_area != "", Person.land_area.isnot(None))
    elif filter_value == "空白":
        return query.filter(
            (Person.land_area == "") | (Person.land_area.is_(None))
        )
    return query
