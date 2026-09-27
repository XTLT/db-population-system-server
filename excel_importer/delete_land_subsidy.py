from database import get_session, LandSubsidy


def delete_land_subsidy(subsidy_id: str):

    session = get_session()
    try:
        subsidy = session.query(LandSubsidy).filter(LandSubsidy.id == subsidy_id).first()
        if subsidy:
            session.delete(subsidy)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
