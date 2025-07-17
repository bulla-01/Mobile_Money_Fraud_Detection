from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from database import Base
from sqlalchemy.ext.declarative import declarative_base
from models import Regtb

class Transaction(Base):
    __tablename__ = "transactiontb"

    id = Column(Integer, primary_key=True, index=True)
    trxdate = Column(DateTime)
    type = Column(String)
    amount = Column(Float)
    nameOrig = Column(String)
    oldbalanceOrg = Column(Float)
    newbalanceOrig = Column(Float)
    nameDest = Column(String)
    beneficiaryname = Column(String)
    oldbalanceDest = Column(Float)
    newbalanceDest = Column(Float)
    mobilenetwork = Column(String)
    
Base = declarative_base()

class Regtb(Base):
    __tablename__ = 'regtb'

    phoneno = Column(String, primary_key=True, nullable=False)
    full_name = Column(String)
    dob = Column(Date)
    email = Column(String)
    house_address = Column(String)
    id_no = Column(String)
    tin = Column(String)
    next_of_kin = Column(String)
    next_contact = Column(String)
    pin = Column(String(4))


