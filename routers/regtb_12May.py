#regtblll.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from queries import get_beneficiary_by_phone, get_initiator_balance_by_phone
from database import get_db
from schemas import BeneficiaryResponse, BalanceResponse
from sqlalchemy import Column, Integer, String, Date, Float, Numeric, DateTime

router = APIRouter()

# Endpoint to validate beneficiary (existing)
@router.get("/validate-beneficiary/{beneficiary_number}", response_model=BeneficiaryResponse)
async def validate_beneficiary(
    beneficiary_number: str,
    db: Session = Depends(get_db)
):
    beneficiary = get_beneficiary_by_phone(db, beneficiary_number)
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    return {
        "success": True,
        "full_name": beneficiary.full_name,
    }

#Endpoint to fetch the initiator balance
@router.get("/validate-initiator/{phone_number}", response_model=BalanceResponse)
async def get_initiator_balance(
    phone_number: str,
    db: Session = Depends(get_db)
):
    # Fetch the balance for the initiator by phone number
    balance = get_initiator_balance_by_phone(db, phone_number)
    if not balance:
        raise HTTPException(status_code=404, detail="Initiator not found")
    
    return {
        "success": True,
        "balance": balance
    }


# @router.get("/validate-initiator/{phone_number}")
# def validate_initiator(phone_number: str, db: Session = Depends(get_db)):
    # # Get the latest transaction for this specific initiator
    # transaction = (
        # db.query(TransactionModel)
        # .filter(TransactionModel.nameOrig == phone_number)
        # .order_by(TransactionModel.trxdate.desc())
        # .first()
    # )

    # if not transaction:
        # raise HTTPException(status_code=404, detail="Initiator not found")

    # # Get the full name from the regtblll table
    # reg = db.query(regtblll).filter(regtblll.phoneno == phone_number).first()
    # full_name = reg.full_name if reg else "Unknown"

    # return {
        # "success": True,
        # "phone_number": phone_number,
        # "full_name": full_name,
        # "balance": transaction.newbalanceOrig
    # }
