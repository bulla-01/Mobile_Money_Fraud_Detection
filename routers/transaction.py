from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import uuid
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, SessionLocal, test_db_connection
from models import Transaction1, RegTbl, ComplianceTbl
from predict import predict_fraud, send_fraud_alert_email
from datetime import datetime, timezone
from dateutil import parser
import logging

router = APIRouter()

# ---------- Pydantic Input Model ----------
class TransactionData(BaseModel):
    trxdate: str
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    beneficiaryname: str
    oldbalanceDest: float
    newbalanceDest: float
    mobilenetwork: str
    transactionstatus: str
    
# ---------- Pydantic Input Model - Registration ----------
class TransactionData2(BaseModel):
    phone_number: str
    fullname: str
    date_of_birth: str
    email: str
    house_address: str
    latitude: float
    longitude: float
    id_number: str
    tin: str
    next_of_kin: str
    next_of_kin_phone: str
    pin: str

# ---------- Pydantic Input Model - Admin----------
class TransactionData3(BaseModel):
    full_name: str
    email: str
    status: str
    department: str
    created_by: str
    date_created: str

@router.post("/transactions/submit", operation_id="submit_transaction")
async def submit_transaction(transaction: TransactionData, db: Session = Depends(get_db)):
    try:
        now = datetime.now(timezone.utc)
        status = transaction.transactionstatus.upper()

        # Compute new balances
        if status == "SUCCESSFUL":
            newbalanceOrig = transaction.oldbalanceOrg - transaction.amount
            newbalanceDest = transaction.oldbalanceDest + transaction.amount
            message = "Transaction submitted successfully"
        elif status == "PENDING":
            newbalanceOrig = transaction.oldbalanceOrg
            newbalanceDest = transaction.oldbalanceDest
            message = "TRANSACTION PENDING, KINDLY CONTACT THE CONTACT CENTER ON 0244474327"
        else:
            raise HTTPException(status_code=400, detail="Invalid transactionstatus value")

        # Build full transaction dictionary for prediction
        txn_dict = transaction.dict()
        txn_dict["newbalanceOrig"] = newbalanceOrig
        txn_dict["newbalanceDest"] = newbalanceDest

        # Run fraud prediction
        is_fraud, risk_score, reason, label = predict_fraud(txn_dict)

        # Save transaction to database
        transaction_record = Transaction1(
            trxdate=now,
            step=transaction.step,
            type=transaction.type,
            amount=transaction.amount,
            nameOrig=transaction.nameOrig,
            oldbalanceOrg=transaction.oldbalanceOrg,
            newbalanceOrig=newbalanceOrig,
            nameDest=transaction.nameDest,
            oldbalanceDest=transaction.oldbalanceDest,
            newbalanceDest=newbalanceDest,
            mobilenetwork=transaction.mobilenetwork,
            beneficiaryname=transaction.beneficiaryname,
            transactionstatus=status
        )

        db.add(transaction_record)
        db.commit()
        db.refresh(transaction_record)

        # Save prediction to database
        save_prediction_to_db(txn_dict, {
            "is_fraud": is_fraud,
            "risk_score": risk_score,
            "label": label
        }, reason)

        # Send alert if fraud
        if is_fraud:
            send_fraud_alert_email(txn_dict, is_fraud, risk_score, reason, db)

        return {
            "message": message,
            "id": transaction_record.id,
            "fraud": bool(is_fraud),
            "risk_score": risk_score,
            "reason": reason
        }

    except Exception as e:
        logging.error(f"❌ Transaction failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transaction submission failed: {str(e)}")

# ---------- Save Prediction to DB ----------
def save_prediction_to_db(txn_dict: dict, prediction_response: dict, description: str):
    db = SessionLocal()
    test_db_connection()
    try:
        trx_datetime = parser.isoparse(txn_dict['trxdate']) if isinstance(txn_dict['trxdate'], str) else txn_dict['trxdate']

        prediction_record = PredictionAnalysis(
            step=txn_dict['step'],
            type=txn_dict['type'],
            amount=txn_dict['amount'],
            nameorig=txn_dict['nameOrig'],
            oldbalanceorg=txn_dict['oldbalanceOrg'],
            newbalanceorig=txn_dict['newbalanceOrig'],
            namedest=txn_dict['nameDest'],
            oldbalancedest=txn_dict['oldbalanceDest'],
            newbalancedest=txn_dict['newbalanceDest'],
            trxdate=trx_datetime,
            beneficiaryname=txn_dict['beneficiaryname'],
            mobilenetwork=txn_dict['mobilenetwork'],
            prediction_response=prediction_response,
            prediction_description=description,
            is_fraud=prediction_response.get("is_fraud"),
            fraud_probability=prediction_response.get("risk_score"),
            prediction_label=prediction_response.get("label")
        )

        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)
        logging.info(f"✅ Prediction saved with ID: {prediction_record.id}")

    except Exception as e:
        db.rollback()
        logging.error(f"❌ Error saving prediction data: {e}")
    finally:
        db.close()
        
# ---------- Save Registration to DB ----------
@router.post("/new_registration/submit", operation_id="submit_reg")
async def submit_new_registration(transaction: TransactionData2, db: Session = Depends(get_db)):
    try:
        
        # Save transaction
        transaction_record = RegTbl(
            phone_number = transaction.phone_number,
            fullname=transaction.fullname,
            date_of_birth=transaction.date_of_birth,
            email=transaction.email,
            house_address=transaction.house_address,
            latitude=transaction.latitude,
            longitude=transaction.longitude,
            tin=transaction.tin,
            next_of_kin=transaction.next_of_kin,
            next_of_kin_phone=transaction.next_of_kin_phone,
            pin=transaction.pin
           )

        db.add(transaction_record)
        db.commit()
        db.refresh(transaction_record)
        
        return {"success": True}

    except Exception as e:
        logging.error(f"❌ Registration Failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration submission failed: {str(e)}")
        
        
# ---------- Save Admin Users to DB ----------

from datetime import datetime

@router.post("/create_admin/submit", operation_id="submit_user")
async def create_admin(transaction: TransactionData3, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        existing_user = db.query(ComplianceTbl).filter_by(email=transaction.email).first()
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Email already registered"}
            )

        # Convert date_created string to datetime
        if isinstance(transaction.date_created, str):
            try:
                transaction_date = datetime.strptime(transaction.date_created, "%Y-%m-%d")
            except ValueError:
                return JSONResponse(
                    status_code=422,
                    content={"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}
                )
        else:
            transaction_date = transaction.date_created

        # Create new user
        new_user = ComplianceTbl(
            user_id=str(uuid.uuid4())[:8],
            full_name=transaction.full_name,
            email=transaction.email,
            status=transaction.status,
            department=transaction.department,
            created_by=transaction.created_by,
            date_created=transaction_date
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "User created"}
        )

    except Exception as e:
        print("Error:", e)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to create user"}
        )
