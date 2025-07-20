import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Routers and local modules
from routers import status, transaction, suspicious
from routers.initiator import router as initiator_router
import regtb
import validate_initiator
import initiator_location
import my_emails
# from analysis_fastapi import router as analysis_router
from database import get_db, init_db
from predict import preprocess_input, predict_fraud, send_fraud_alert_email
from db_ops import insert_transaction
from db_connection import get_db_connection

# ==================== FastAPI App Initialization ====================
app = FastAPI(
    title="📈 MOMO Fraud Detection API",
    version="1.0",
    description="Fraud prediction using MLP + XGBoost + Random Forest ensemble."
)

# ==================== Logging Setup ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app_logs.log"),
        logging.StreamHandler()
    ]
)

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Startup DB Init ====================
@app.on_event("startup")
def startup_event():
    logging.info("🚀 Starting app... Initializing database...")
    init_db()
    logging.info("✅ Database initialized successfully.")

# ==================== Pydantic Schema ====================
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

# ==================== Root Endpoint ====================
@app.get("/")
def read_root():
    return {"message": "Welcome to the Fraud Detection API"}

# ==================== /predict Endpoint ====================
@app.post("/predict")
async def predict_transaction(request: Request, db: Session = Depends(get_db)):
    try:
        txn = await request.json()
        logging.info(f"📩 Received transaction: {txn}")

        is_fraud, risk_score, reason, rule_detail, status = predict_fraud(txn)

        insert_transaction(txn, is_fraud, risk_score, status, db)

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
        logging.error(f"❌ Prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

# ==================== Include All Routers ====================
app.include_router(transaction.router)
app.include_router(status.router)
app.include_router(initiator_router)
app.include_router(validate_initiator.router)
app.include_router(regtb.router)
app.include_router(initiator_location.router)
# app.include_router(analysis_router)
app.include_router(suspicious.router)
app.include_router(my_emails.router)
