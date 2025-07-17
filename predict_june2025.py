from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from models import ComplianceTbl
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
import logging
import smtplib
from email.message import EmailMessage
from collections import defaultdict
from datetime import datetime, timedelta
from config import settings
import os

logging.basicConfig(level=logging.INFO)

EMAIL_USER = settings.EMAIL_USER
EMAIL_PASS = settings.EMAIL_PASS

user_tx_times = defaultdict(list)

# ========== Check File Existence and Load Models ==========

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

encoder_model = None
if check_file("lstm_encoder.h5"):
    try:
        encoder_model = load_model("lstm_encoder.h5")
        logging.info("✅ LSTM encoder loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Error loading LSTM encoder: {e}")

rf_model = None
if check_file("rf_lstm.pkl"):
    try:
        rf_model = joblib.load("rf_lstm.pkl")
        logging.info("✅ Random Forest model loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Error loading RF model: {e}")

# ========== Preprocessing ==========
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

    df.drop(columns=[
        "nameOrig", "nameDest", "type", "trxdate", "mobilenetwork", "beneficiaryname"
    ], errors='ignore', inplace=True)

    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_columns]

    if scaler is None:
        raise RuntimeError("Scaler not loaded")

    scaled = scaler.transform(df)
    return scaled

# ========== Frequency Rule ==========
def check_user_frequency(txn):
    user = txn["nameOrig"]
    now = datetime.fromisoformat(txn["trxdate"].replace("Z", "+00:00"))
    recent_times = [t for t in user_tx_times[user] if now - t < timedelta(hours=1)]
    recent_times.append(now)
    user_tx_times[user] = recent_times
    return len(recent_times)

# ========== Prediction ==========
def predict_fraud(txn: dict) -> tuple[int, float, str, str, str]:
    if txn["amount"] > 1e8 or txn["newbalanceOrig"] < 0:
        return (1, 1.0, "High amount or negative balance", "Rule-based: High amount or negative balance", "PENDING")

    if check_user_frequency(txn) > 10:
        return (1, 0.95, "Unusual transaction frequency", "Rule-based: Unusual transaction frequency", "PENDING")

    if encoder_model is None or rf_model is None:
        raise RuntimeError("LSTM encoder or RF model not loaded")

    preprocessed = preprocess_input(txn)
    preprocessed_lstm = prepr_
