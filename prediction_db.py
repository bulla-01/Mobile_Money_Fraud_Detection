#prediction_db.py
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from dateutil import parser
import os
from models import Base  # Import Base only from models

# Define the base for SQLAlchemy
Base = declarative_base()

# Define the model for the new table to save predictions
class PredictionAnalysis(Base):
    __tablename__ = 'prediction_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    step = Column(Integer)
    type = Column(String(50))
    amount = Column(Float)
    nameorig = Column(String(100))  # ← lowercase
    oldbalanceorg = Column(Float)
    newbalanceorig = Column(Float)
    namedest = Column(String(100))
    oldbalancedest = Column(Float)
    newbalancedest = Column(Float)
    trxdate = Column(DateTime)
    beneficiaryname = Column(String(100))
    mobilenetwork = Column(String(50))
    prediction_response = Column(JSONB)
    prediction_description = Column(String(50))
    prediction_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)

# Database URL and Engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@db:5432/fraud_db")
print("DATABASE_URL:", DATABASE_URL)

engine = create_engine(DATABASE_URL)

# SessionLocal: to create sessions in your API endpoints
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to test the DB connection
from sqlalchemy import text

def test_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Database connection successful. Result: {result.scalar()}")
    except Exception as e:
        print(f"Database connection failed: {e}")


# Function to create the tables in the database 
def create_tables():
    Base.metadata.create_all(bind=engine)



# Function to save the prediction data
def save_prediction_to_db(txn_dict, prediction_response, description):
    db = SessionLocal()
    test_db_connection()

    try:
        trx_datetime = parser.isoparse(txn_dict['trxdate']) if isinstance(txn_dict['trxdate'], str) else txn_dict['trxdate']

        print(f"Prediction Response: {prediction_response}")

        # Extract values from prediction_response if it's a dict
        if isinstance(prediction_response, dict):
            is_fraud = prediction_response.get("is_fraud", None)
            fraud_probability = prediction_response.get("risk_score", None)
            prediction_label = prediction_response.get("label", None)
        else:
            is_fraud = None
            fraud_probability = None
            prediction_label = None

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
            prediction_response=prediction_response,  # raw dict or json
            prediction_description=description,
            is_fraud=is_fraud,
            fraud_probability=fraud_probability,
            prediction_label=prediction_label
        )

        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)

        print(f"Prediction saved with ID: {prediction_record.id}")

    except Exception as e:
        db.rollback()
        print(f"[X] Error saving prediction data: {e}")

    finally:
        db.close()
