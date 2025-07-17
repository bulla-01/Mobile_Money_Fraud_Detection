from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf

# routers/predict.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/predict")
def predict():
    return {"message": "Prediction endpoint"}

# FastAPI app
app = FastAPI(title="MOMO Fraud Detection API")

# Load models
mlp_encoder = tf.keras.models.load_model("mlp_encoder.h5")  # The encoder part of MLP
ensemble_model = joblib.load("xgb_sklearn_wrapper.pkl")     # VotingClassifier (XGB + RF)
scaler = joblib.load("scaler.pkl")

# Input schema
class TransactionInput(BaseModel):
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float

def preprocess_input(txn: dict):
    df = pd.DataFrame([txn])

    # Extract numeric from ID
    df["nameOrig_numeric"] = df["nameOrig"].str.extract(r"(\d+)").astype(int)
    df["nameDest_numeric"] = df["nameDest"].str.extract(r"(\d+)").astype(int)

    # One-hot encode 'type'
    type_dummies = pd.get_dummies(df["type"], prefix='type', dtype=int)
    df = pd.concat([df, type_dummies], axis=1)

    # Feature Engineering
    df["trx_bal_origin"] = df["oldbalanceOrg"] - df["newbalanceOrig"]
    df["trx_bal_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]
    df["origin_amt_ratio"] = df["amount"] / (df["oldbalanceOrg"] + 1)
    df["dest_amt_ratio"] = df["amount"] / (df["oldbalanceDest"] + 1)
    df["origin_old_zero"] = (df["oldbalanceOrg"] == 0).astype(int)
    df["origin_new_zero"] = (df["newbalanceOrig"] == 0).astype(int)
    df["dest_old_zero"] = (df["oldbalanceDest"] == 0).astype(int)
    df["dest_new_zero"] = (df["newbalanceDest"] == 0).astype(int)
    df["trx_per_user"] = 1  # Placeholder
    df["average_amt_per_user"] = df["amount"]  # Placeholder
    df["large_value_flag"] = ((df.get("type_TRANSFER", 0) == 1) & (df["amount"] > 200000)).astype(int)
    df["flag_empty_dest"] = ((df["newbalanceDest"] == 0) & (df["amount"] > 0)).astype(int)

    # Drop unnecessary columns
    df.drop(columns=["nameOrig", "nameDest", "oldbalanceOrg", "newbalanceOrig",
                     "oldbalanceDest", "newbalanceDest", "type"], inplace=True, errors='ignore')

    # Ensure all type_* columns exist
    expected_type_cols = ["type_CASH_OUT", "type_PAYMENT", "type_CASH_IN", "type_TRANSFER", "type_DEBIT"]
    for col in expected_type_cols:
        if col not in df.columns:
            df[col] = 0

    # Reorder columns
    df = df.reindex(sorted(df.columns), axis=1)

    # Scale features
    scaled = scaler.transform(df)
    return scaled

@app.post("/predict")
def predict(txn: TransactionInput):
    try:
        txn_dict = txn.dict()
        preprocessed = preprocess_input(txn_dict)

        # Get encoded features from MLP encoder
        encoded_features = mlp_encoder.predict(preprocessed)

        # Predict using VotingClassifier ensemble
        prediction = ensemble_model.predict(encoded_features)[0]

        return {"fraud_prediction": int(prediction)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
