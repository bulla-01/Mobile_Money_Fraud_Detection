#analysis_schema.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransactionInput(BaseModel):
    trxdate: str
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float
    mobilenetwork: str
    beneficiaryname: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None



class TransactionOutput(BaseModel):
    id: int
    trxdate: datetime
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float
    mobilenetwork: str
    beneficiaryname: str

    class Config:
        orm_mode = True


class PredictionResponse(BaseModel):
    is_fraud: bool
    probability: float
    label: str
    description: str
    prediction_id: Optional[int] = None


class PredictionAnalysisSchema(BaseModel):
    id: int
    step: int
    type: str
    amount: float
    nameorig: str
    oldbalanceorg: float
    newbalanceorig: float
    namedest: str
    oldbalancedest: float
    newbalancedest: float
    trxdate: datetime
    beneficiaryname: str
    mobilenetwork: str
    prediction_description: str
    prediction_date: datetime
    prediction_response: dict
    is_fraud: bool
    fraud_probability: float
    prediction_label: str

    class Config:
        orm_mode = True
