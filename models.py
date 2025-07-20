from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, Numeric, func
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import JSON
from typing import List, Optional
from decimal import Decimal


Base = declarative_base()

# class RiskUser(Base):
    # __tablename__ = "risk_users"

    # id = Column(Integer, primary_key=True, index=True)
    # namedest = Column(String, nullable=False)
    # fraud_probability = Column(Float, nullable=False)
    
class RegTbl(Base):
    __tablename__ = "regtbl"

    phone_number = Column(String, primary_key=True, nullable=False)
    fullname = Column(String)
    date_of_birth = Column(Date)
    email = Column(String)
    house_address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    id_number = Column(String)
    tin = Column(String)
    next_of_kin = Column(String)
    next_of_kin_phone = Column(String)
    pin = Column(String(4))


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    step = Column(Integer)
    type = Column(String(50))
    amount = Column(Float)
    nameOrig = Column(String(255))
    oldbalanceOrg = Column(Float)
    newbalanceOrig = Column(Float)
    nameDest = Column(String(255))
    oldbalanceDest = Column(Float)
    newbalanceDest = Column(Float)
    isFraud = Column(Integer)


class Transaction1(Base):
    __tablename__ = 'transactiontbl'

    id = Column(Integer, primary_key=True, index=True)
    trxdate = Column(DateTime, nullable=False)
    step = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    nameOrig = Column(String(255), nullable=False)
    oldbalanceOrg = Column(Numeric(12, 2))
    newbalanceOrig = Column(Numeric(12, 2))
    nameDest = Column(String(255), nullable=False)
    oldbalanceDest = Column(Numeric(12, 2))
    newbalanceDest = Column(Numeric(12, 2))
    mobilenetwork = Column(String(50))
    beneficiaryname = Column(String(255))
    transactionstatus = Column(String)
    is_fraud = Column(String)
    fraud_probability = Column(String)
    prediction_label = Column(String)
    prediction_description = Column(String)
    prediction_date = Column(Date)
    latitude = Column(Float)
    longitude = Column(Float)

    def __repr__(self):
        return f"<Transaction1(id={self.id}, type='{self.type}', amount={self.amount})>"  

def __repr__(self):
    return f"registration(id={self.id}, type='{self.type}', phone_number={self.phone_number})"

class ComplianceTbl(Base):
    __tablename__ = "compliancetbl"

    user_id = Column(String(50), primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String(100), unique=True, index=True)
    status = Column(String, nullable=False)
    department = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)

# ---------- Pydantic INPUT MODEL ----------

class TransactionData(BaseModel):
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

    class Config:
        from_attributes = True
