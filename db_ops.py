# db_ops.py

from sqlalchemy.orm import Session
from models import Transaction1
from datetime import datetime


def insert_transaction(txn: dict, is_fraud: bool, fraud_probability: float, status: str, db: Session):
    txn_record = Transaction1(
        trxdate=datetime.now(),
        step=txn["step"],
        type=txn["type"],
        amount=txn["amount"],
        nameOrig=txn["nameOrig"],
        oldbalanceOrg=txn["oldbalanceOrg"],
        newbalanceOrig=txn["newbalanceOrig"],
        nameDest=txn["nameDest"],
        oldbalanceDest=txn["oldbalanceDest"],
        newbalanceDest=txn["newbalanceDest"],
        mobilenetwork=txn.get("mobilenetwork"),
        beneficiaryname=txn.get("beneficiaryname"),
        transactionstatus=status,
        is_fraud=is_fraud,
        fraud_probability=fraud_probability
    )
    db.add(txn_record)
    db.commit()
    db.refresh(txn_record)
    return txn_record
