def apply_local_welfare_forest_filter(query, filter_value, Person):
    if filter_value == "不为0":
        return query.filter(Person.local_welfare_forest_area != "", Person.local_welfare_forest_area.isnot(None))
    elif filter_value == "空白":
        return query.filter(
            (Person.local_welfare_forest_area == "") | (Person.local_welfare_forest_area.is_(None))
        )
    return query
