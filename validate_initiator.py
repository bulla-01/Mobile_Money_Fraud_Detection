#validate_initiator.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from queries import get_initiator_balance_by_phone
from database import get_db
from models import Transaction1
#from models import regtbl

router = APIRouter()

@router.get("/validate_initiator/{phone_number}")
def validate_initiator(phone_number: str, db: Session = Depends(get_db)):
    logging.info(f"Validating phone number: {phone_number}")

    # Fetch latest transaction as initiator
    initiator_txn = db.query(Transaction1).filter(Transaction1.nameOrig == phone_number).order_by(Transaction1.id.desc()).first()

    # Fetch latest transaction as beneficiary
    beneficiary_txn = db.query(Transaction1).filter(Transaction1.nameDest == phone_number).order_by(Transaction1.id.desc()).first()

    # Determine latest transaction
    latest_txn = None
    role = None

    if initiator_txn and beneficiary_txn:
        latest_txn = initiator_txn if initiator_txn.id > beneficiary_txn.id else beneficiary_txn
        role = "initiator" if initiator_txn.id > beneficiary_txn.id else "beneficiary"
    elif initiator_txn:
        latest_txn = initiator_txn
        role = "initiator"
    elif beneficiary_txn:
        latest_txn = beneficiary_txn
        role = "beneficiary"

    # Determine balance
    if latest_txn:
        if role == "initiator":
            balance = get_initiator_balance_by_phone(db, phone_number)
        else:
            balance = latest_txn.newbalanceDest

        return {
            "success": True,
            "balance": float(balance) if balance is not None else 0.0
        }
    else:
        return {
            "success": False,
            "message": "Initiator not found"
        }
