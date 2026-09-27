from database import get_session, LandSubsidy


def get_person_subsidy_total(id_card: str, subsidy_year: str = None) -> str:

    session = get_session()
    try:
        query = session.query(LandSubsidy).filter(LandSubsidy.id_card == id_card)
        if subsidy_year:
            query = query.filter(LandSubsidy.year.startswith(subsidy_year))
        subsidies = query.all()
        if not subsidies:
            return ""
        total = 0.0
        for s in subsidies:
            try:
                total += float(s.total_amount)
            except (ValueError, TypeError):
                pass
        return f"{total:.2f}" if total > 0 else ""
    finally:
        session.close()
