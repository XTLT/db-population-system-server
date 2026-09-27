from database import get_session, TreatmentPayment


def get_all_treatment_payments(period: str = None, id_card: str = None, subsidy_type: str = None) -> list:

    session = get_session()
    try:
        query = session.query(TreatmentPayment)
        if period:
            query = query.filter(TreatmentPayment.period == period)
        if id_card:
            safe_id_card = id_card.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            query = query.filter(TreatmentPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if subsidy_type:
            query = query.filter(TreatmentPayment.subsidy_type == subsidy_type)
        return query.order_by(TreatmentPayment.period.desc(), TreatmentPayment.name).all()
    finally:
        session.close()
