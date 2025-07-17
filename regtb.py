# regtb.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from queries import get_beneficiary_by_phone
from database import get_db
from schemas import BeneficiaryResponse

router = APIRouter()

@router.get("/validate-beneficiary/{phoneno}", response_model=BeneficiaryResponse)
async def validate_beneficiary(phoneno: str, db: Session = Depends(get_db)):
    beneficiary = get_beneficiary_by_phone(db, phoneno)
    
    if beneficiary:
        return {"success": True, "full_name": beneficiary.fullname}
    else:
        raise HTTPException(status_code=404, detail="Beneficiary not found")


