from database import get_session, TreatmentPayment


def delete_treatment_payment(payment_id: str):

    session = get_session()
    try:
        payment = session.query(TreatmentPayment).filter(TreatmentPayment.id == payment_id).first()
        if payment:
            session.delete(payment)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
