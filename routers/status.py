# routers/status.py

import os
from fastapi import APIRouter, HTTPException
from database import SessionLocal  # make sure you have SessionLocal imported correctly
from database import init_db

# Initialize the database (create tables if they don't exist)
init_db()

router = APIRouter()

@router.get("/status")
def get_status():
    try:
        # Basic health checks
        encoder_ok = os.path.exists("mlp_encoder.h5")
        ensemble_ok = os.path.exists("xgb_sklearn_wrapper.pkl")
        scaler_ok = os.path.exists("scaler.pkl")

        db_status = "unknown"
        try:
            # Try simple DB connection
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            db_status = "connected"
        except Exception:
            db_status = "disconnected"

        return {
            "status": "ok",
            "models": {
                "mlp_encoder_loaded": encoder_ok,
                "ensemble_model_loaded": ensemble_ok,
                "scaler_loaded": scaler_ok
            },
            "database": db_status,
            "message": "🚀 Fraud Detection System is up and running!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")
