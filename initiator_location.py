#initiator_location.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import RegTbl  

router = APIRouter()

@router.get("/initiator_location/{phone_number}")
def initiator_location(phone_number: str, db: Session = Depends(get_db)):
    location = db.query(regtbl).filter(regtbl.phone_number == phone_number).first()

    if location and location.latitude is not None and location.longitude is not None:
        return {
            "success": True,
            "latitude": location.latitude,
            "longitude": location.longitude
        }
    else:
        raise HTTPException(status_code=404, detail="Initiator's location not found")
