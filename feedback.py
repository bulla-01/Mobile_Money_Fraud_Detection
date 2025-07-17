# feedback.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Float, String, Table, MetaData
from sqlalchemy.orm import sessionmaker
from database import engine  # ✅ Centralized engine import

app = FastAPI()

metadata = MetaData()

# Define the feedback table
feedback_table = Table(
    "feedback", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("step", Integer),
    Column("type", String),
    Column("amount", Float),
    Column("nameOrig", String),
    Column("oldbalanceOrg", Float),
    Column("newbalanceOrig", Float),
    Column("nameDest", String),
    Column("oldbalanceDest", Float),
    Column("newbalanceDest", Float),
    Column("isFraud", Integer)
)

# ✅ Use centralized engine
metadata.create_all(engine)

# ✅ Use centralized engine again
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the request schema
class FeedbackInput(BaseModel):
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float
    isFraud: int

@app.post("/feedback")
def feedback(feedback: FeedbackInput):
    try:
        db = SessionLocal()
        insert_query = feedback_table.insert().values(**feedback.dict())
        db.execute(insert_query)
        db.commit()
        db.close()
        return {"message": "✅ Feedback saved to PostgreSQL database successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Error saving feedback: {e}")
