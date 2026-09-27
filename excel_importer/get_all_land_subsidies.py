from database import get_session, LandSubsidy


def get_all_land_subsidies(subsidy_year: str = None) -> list:

    session = get_session()
    try:
        query = session.query(LandSubsidy)
        if subsidy_year:
            query = query.filter(LandSubsidy.year == subsidy_year)
        return query.order_by(LandSubsidy.name).all()
    finally:
        session.close()
