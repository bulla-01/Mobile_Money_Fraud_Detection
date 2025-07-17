# config.py

from pydantic_settings import BaseSettings
from datetime import date
from pydantic import BaseModel


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:Bentjun25%24@db:5432/momo_db"
    EMAIL_USER: str
    EMAIL_PASS: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Instantiate once and import `settings` wherever needed
settings = Settings()

class HighRiskUserOut(BaseModel):
    name: str
    fraud_score: float
    from_: date
    to: date

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
        }
