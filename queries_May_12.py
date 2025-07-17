# queries.py

from sqlalchemy.orm import Session
from database import feedback_table
from database import transactiontb
from sqlalchemy import insert
from models import regtbl

def get_beneficiary_by_phone(db: Session, phoneno: str):
    all_beneficiaries = db.query(regtbl).all()
    print("All beneficiaries:")
    for b in all_beneficiaries:
        print(b.phone_number)
    return db.query(regtbl).filter(regtbl.phone_number == phoneno).first()


def create_transaction(db: Session, transaction_data: dict):
    insert_stmt = transactiontb.insert().values(**transaction_data)
    db.execute(insert_stmt)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

# -------- INSERT into feedback table --------
def create_feedback(db: Session, feedback_data: dict):
    insert_stmt = feedback_table.insert().values(**feedback_data)
    db.execute(insert_stmt)
    db.commit()

# -------- SELECT from feedback table --------
def get_feedback(db: Session, feedback_id: int = None):
    if feedback_id:
        query = feedback_table.select().where(feedback_table.c.id == feedback_id)
    else:
        query = feedback_table.select()
    result = db.execute(query)
    return result.fetchall()

# -------- UPDATE feedback table --------
def update_feedback(db: Session, feedback_id: int, update_data: dict):
    update_stmt = feedback_table.update().where(feedback_table.c.id == feedback_id).values(**update_data)
    db.execute(update_stmt)
    db.commit()

# -------- DELETE from feedback table --------
def delete_feedback(db: Session, feedback_id: int):
    delete_stmt = feedback_table.delete().where(feedback_table.c.id == feedback_id)
    db.execute(delete_stmt)
    db.commit()
