# schemas.py
from pydantic import BaseModel

class BeneficiaryResponse(BaseModel):
    success: bool
    full_name: str

    class Config:
        orm_mode = True

class BalanceResponse(BaseModel):
    success: bool
    balance: float
