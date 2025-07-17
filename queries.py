from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Feedback, Transaction1, RegTbl
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -------------- GET Beneficiary ----------------
def get_beneficiary_by_phone(db: Session, phoneno: str):
    try:
        all_beneficiaries = db.query(RegTbl).all()
        logger.debug(f"Beneficiaries count: {len(all_beneficiaries)}")
        return db.query(RegTbl).filter(RegTbl.phone_number == phoneno).first()
    except Exception as e:
        logger.error(f"Error fetching beneficiary by phone {phoneno}: {e}")
        return None

# -------------- GET Initiator Balance ----------------

def get_initiator_balance_by_phone(db: Session, phone_number: str):
    try:
        transaction = (
            db.query(Transaction1)
            .filter(Transaction1.nameOrig == phone_number)
            .order_by(Transaction1.trxdate.desc())
            .first()
        )
        if transaction:
            return transaction.newbalanceOrig
        return None
    except Exception as e:
        logger.error(f"Error fetching initiator balance for phone {phone_number}: {e}")
        return None

# -------------- GET Initiator Location ----------------

def get_initiator_location_by_phone(db: Session, phone_number: str):
    try:
        location = db.query(regtbl).filter(regtbl.phone_number == phone_number).first()
        if location and location.latitude is not None and location.longitude is not None:
            return location.latitude, location.longitude
        return None
    except Exception as e:
        logger.error(f"Error fetching initiator location for phone {phone_number}: {e}")
        return None

# -------------- CREATE Feedback ----------------

def create_feedback(db: Session, feedback_data: dict):
    try:
        feedback = Feedback(**feedback_data)
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating feedback: {e}")
        raise

# -------------- GET Feedback ----------------

def get_feedback(db: Session, feedback_id: int = None):
    try:
        if feedback_id:
            query = select(Feedback).where(Feedback.id == feedback_id)
        else:
            query = select(Feedback)
        result = db.execute(query)
        return result.scalars().all()  # returns list of Feedback ORM objects
    except Exception as e:
        logger.error(f"Error fetching feedback(s): {e}")
        return []

# -------------- UPDATE Feedback ----------------

def update_feedback(db: Session, feedback_id: int, update_data: dict):
    try:
        update_stmt = Feedback.__table__.update().where(Feedback.id == feedback_id).values(**update_data)
        db.execute(update_stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating feedback id {feedback_id}: {e}")
        raise

# -------------- DELETE Feedback ----------------

def delete_feedback(db: Session, feedback_id: int):
    try:
        delete_stmt = Feedback.__table__.delete().where(Feedback.id == feedback_id)
        db.execute(delete_stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting feedback id {feedback_id}: {e}")
        raise
