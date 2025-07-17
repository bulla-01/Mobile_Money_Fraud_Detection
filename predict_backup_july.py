#predict.py

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from models import ComplianceTbl
import pandas as pd
import numpy as np
import joblib
import logging
import smtplib
from email.message import EmailMessage
from collections import defaultdict, deque
from datetime import datetime, timedelta
import os
from config import settings
from tensorflow.keras.models import load_model

# ==================== Logging ====================
logging.basicConfig(level=logging.INFO)

EMAIL_USER = settings.EMAIL_USER
EMAIL_PASS = settings.EMAIL_PASS

# ==================== In-memory Tracker ====================
user_tx_times = defaultdict(lambda: deque(maxlen=50))

# ==================== Load Models and Assets ====================
def check_file(path):
    if not os.path.exists(path):
        logging.error(f"❌ File not found: {path}")
        return False
    logging.info(f"✅ File exists: {path}")
    return True

feature_columns = []
if check_file("feature_columns.pkl"):
    try:
        feature_columns = joblib.load("feature_columns.pkl")
        logging.info("✅ Feature columns loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Error loading feature columns: {e}")

scaler = None
if check_file("scaler.pkl"):
    try:
        scaler = joblib.load("scaler.pkl")
        logging.info("✅ Scaler loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Error loading scaler: {e}")

# encoder_model = None
# if check_file("lstm_encoder.h5"):
    # try:
        # encoder_model = load_model("lstm_encoder.h5")
        # logging.info("✅ LSTM encoder loaded successfully.")
    # except Exception as e:
        # logging.error(f"❌ Error loading LSTM encoder: {e}")

rf_model = None
if check_file("randomforest.pkl"):
    try:
        rf_model = joblib.load("randomforest.pkl")
        logging.info("✅ Random Forest model loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Error loading RF model: {e}")

# ==================== Preprocessing ====================
def preprocess_input(txn: dict):
    df = pd.DataFrame([txn])

    df["nameOrig_numeric"] = df["nameOrig"].str.extract(r"(\d+)").astype(float)
    df["nameDest_numeric"] = df["nameDest"].str.extract(r"(\d+)").astype(float)

    df["type"] = df["type"].str.upper()
    type_dummies = pd.get_dummies(df["type"], prefix="type", dtype=int)
    df = pd.concat([df, type_dummies], axis=1)

    df["trx_bal_origin"] = df["oldbalanceOrg"] - df["newbalanceOrig"]
    df["trx_bal_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]
    df["origin_amt_ratio"] = df["amount"] / (df["oldbalanceOrg"] + 1)
    df["dest_amt_ratio"] = df["amount"] / (df["oldbalanceDest"] + 1)
    df["origin_old_zero"] = (df["oldbalanceOrg"] == 0).astype(int)
    df["origin_new_zero"] = (df["newbalanceOrig"] == 0).astype(int)
    df["dest_old_zero"] = (df["oldbalanceDest"] == 0).astype(int)
    df["dest_new_zero"] = (df["newbalanceDest"] == 0).astype(int)
    df["trx_per_user"] = 1
    df["average_amt_per_user"] = df["amount"]
    df["large_value_flag"] = ((df.get("type_TRANSFER", 0) == 1) & (df["amount"] > 200000)).astype(int)
    df["flag_empty_dest"] = ((df["newbalanceDest"] == 0) & (df["amount"] > 0)).astype(int)

    df.drop(columns=["nameOrig", "nameDest", "type", "trxdate", "mobilenetwork", "beneficiaryname"], errors='ignore', inplace=True)

    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_columns]

    if scaler is None:
        logging.error("Scaler not loaded — cannot transform input.")
        raise RuntimeError("Scaler not loaded")

    try:
        scaled = scaler.transform(df)
    except Exception as e:
        logging.error(f"Scaler transform error: {e}")
        raise

    return scaled

# ==================== Frequency Rule ====================
def check_user_frequency(txn):
    user = txn.get("nameOrig")
    try:
        now = datetime.fromisoformat(txn["trxdate"].replace("Z", "+00:00"))
    except Exception as e:
        logging.error(f"Invalid trxdate format: {txn['trxdate']}")
        return 0

    recent_times = [t for t in user_tx_times[user] if now - t < timedelta(hours=1)]
    recent_times.append(now)
    user_tx_times[user] = deque(recent_times, maxlen=50)
    return len(recent_times)

# ==================== Fraud Prediction ====================
def predict_fraud(txn: dict) -> tuple[int, float, str, str, str]:
    if rf_model is None or scaler is None:
        logging.error("Model/scaler not loaded. Aborting fraud prediction.")
        raise RuntimeError("Required model components not loaded.")

    # Rule-based fraud checks
    if txn["amount"] > 1e8 or txn["newbalanceOrig"] < 0:
        logging.warning(f"Rule-based fraud: High amount or negative balance. Txn: {txn}")
        return (
            1,
            1.0,
            "High amount or negative balance",
            "Rule-based: High amount or negative balance",
            "PENDING"
        )

    if check_user_frequency(txn) > 10:
        logging.warning(f"Rule-based fraud: User {txn['nameOrig']} exceeded 10 txns in 1 hour.")
        return (
            1,
            0.95,
            "Unusual transaction frequency",
            "Rule-based: Unusual transaction frequency",
            "PENDING"
        )

    try:
        preprocessed = preprocess_input(txn)
        logging.info(f"Preprocessed features: {preprocessed}")
        
        prob = rf_model.predict_proba(preprocessed)[0][1]

        if np.isnan(prob):
            logging.warning("Model returned NaN for fraud probability. Defaulting to 0.0.")
            prob = 0.0

    except Exception as e:
        logging.error(f"ML prediction failed: {e}")
        raise

    logging.info(f"User {txn['nameOrig']} - Fraud probability: {prob:.4f}")

    is_fraud = int(prob > 0.6)
    status = "PENDING" if is_fraud else "SUCCESSFUL"

    return (
        is_fraud,
        round(float(prob), 4),
        "ML model prediction",
        "ML-based: Probability > 0.6",
        status
    )

# ==================== Email Alert ====================
def send_fraud_alert_email(txn, is_fraud: int, risk_score: float, reason: str, db: Session):
    try:
        active_emails = db.query(ComplianceTbl.email).filter(ComplianceTbl.status == 'ACTIVE').all()
        email_list = [email for (email,) in active_emails]

        if not email_list:
            logging.warning("No active compliance emails found.")
            return

        msg = EmailMessage()
        msg["Subject"] = "🚨 Fraudulent Transaction Detected"
        msg["From"] = EMAIL_USER
        msg["To"] = ", ".join(email_list)

        message = f"""
🚨 *FRAUD ALERT*

A potentially fraudulent transaction was detected.

📅 **Date:** {txn.get('trxdate')}
📱 **Initiator:** {txn.get('nameOrig')}
👤 **Beneficiary:** {txn.get('beneficiaryname')} ({txn.get('nameDest')})
💵 **Amount:** GHS {txn.get('amount')}
📡 **Mobile Network:** {txn.get('mobilenetwork')}
📍 **Location:** Lat {txn.get('latitude')}, Long {txn.get('longitude')}

🔍 **Detection Method:** {reason}
📊 **Risk Score:** {risk_score:.4f}
⚠️ **Flagged as Fraud:** {'YES' if is_fraud else 'NO'}

-------------------------------
📄 Full Transaction Record:
{txn}
"""

        msg.set_content(message)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg, to_addrs=email_list)

        logging.info("✅ Fraud alert email sent successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to send fraud alert email: {e}")
