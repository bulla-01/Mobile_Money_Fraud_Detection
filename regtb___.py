# routers/regtb.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from queries import get_beneficiary_by_phone
from database import get_db  # Assuming this is the function to get the database session
from schemas import BeneficiaryResponse

router = APIRouter()

@router.get("/validate-beneficiary/{phoneno}", response_model=BeneficiaryResponse)
async def validate_beneficiary(phoneno: str, db: Session = Depends(get_db)):
    beneficiary = get_beneficiary_by_phone(phoneno, db)
    
    if beneficiary:
        return {"success": True, "full_name": beneficiary.full_name}
    else:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
        





