import os
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Routers and local modules
from routers import feedback, status, transaction
from routers.initiator import router as initiator_router
import regtb
import validate_initiator
import initiator_location
import analysis_fastapi
from database import get_db
from database import init_db  # ✅ Import init_db
from predict import preprocess_input, predict_fraud, send_fraud_alert_email
from analysis_fastapi import save_prediction_to_db
from db_ops import insert_transaction


app = FastAPI(
    title="📈 MOMO Fraud Detection API",
    version="1.0",
    description="Fraud prediction using MLP + XGBoost + Random Forest ensemble."
)

# ------------------------
# ✅ Logging Setup
# ------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app_logs.log"),
        logging.StreamHandler()
    ]
)

# ------------------------
# ✅ CORS Middleware
# ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # update with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# ✅ Database Initialization on Startup
# ------------------------
@app.on_event("startup")
def startup_event():
    logging.info("🚀 Starting app... Initializing database...")
    init_db()
    logging.info("✅ Database initialized successfully.")

# ------------------------
# ✅ Pydantic Model
# ------------------------
class TransactionInput(BaseModel):
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
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# ------------------------
# ✅ Root Endpoint
# ------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to the Fraud Detection API"}

# ------------------------
# ✅ Prediction Endpoint
# ------------------------
@app.post("/predict")
async def predict_transaction(request: Request, db: Session = Depends(get_db)):
    try:
        txn = await request.json()
        logging.info(f"Received transaction: {txn}")

        is_fraud, risk_score, reason, rule_detail, status = predict_fraud(txn)

        # Log transaction and prediction
        insert_transaction(txn, is_fraud, risk_score, status, db)
      

        # Optional: Send email if fraudulent
        if is_fraud:
            send_fraud_alert_email(txn, is_fraud, risk_score, reason, db)

        return {
            "success": True,
            "is_fraud": is_fraud,
            "risk_score": risk_score,
            "reason": reason,
            "status": status
        }
    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")
        
# ------------------------
# ✅ Include Routers
# ------------------------
app.include_router(transaction.router)
app.include_router(feedback.router)
app.include_router(status.router)
app.include_router(initiator_router)
app.include_router(validate_initiator.router)
app.include_router(regtb.router)
app.include_router(initiator_location.router)
app.include_router(analysis_fastapi.router)
