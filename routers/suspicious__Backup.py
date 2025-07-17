# suspecious.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime
import calendar
from database import get_db
from pydantic import BaseModel

router = APIRouter(
    prefix="/suspicious",
    tags=["suspicious"]
)

class SuspiciousDayCount(BaseModel):
    day: str
    suspicious_count: int

# Utility: Default date handler
def default_start_end_dates(start_date: Optional[str], end_date: Optional[str], default_start: datetime, default_end: datetime):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else default_start
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else default_end
        return start, end
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

# Suspicious transaction count per day
@router.get("/suspicious_transactions_by_day/", response_model=List[SuspiciousDayCount])
def suspicious_transactions_by_day(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1]))

    query = text("""
        SELECT DATE(trxdate) AS day, COUNT(*) AS suspicious_count
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date AND is_fraud = '1'
        GROUP BY day ORDER BY day;
    """)

    result = db.execute(query, {"start_date": start.date(), "end_date": end.date()}).fetchall()
    return [{"day": str(row[0]), "suspicious_count": row[1]} for row in result]

# Total volume of fraudulent transactions
@router.get("/transaction_volume/", response_model=List[Dict])
def get_transaction_volume(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(month=1, day=1), today)

    query = text("""
        SELECT SUM(amount) FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '1';
    """)
    result = db.execute(query, {"start_date": start.date(), "end_date": end.date()}).fetchone()
    volume = float(result[0]) if result[0] is not None else 0.0
    return [{"from": start.date(), "to": end.date(), "volume": volume}]

# Distribution of transaction types
@router.get("/transaction_type_distribution/")
def get_transaction_type_distribution(db: Session = Depends(get_db)):
    query = text("SELECT type, COUNT(*) FROM transactiontbl GROUP BY type;")
    try:
        rows = db.execute(query).fetchall()
        return {"data": [{"type": row[0], "count": row[1]} for row in rows]}
    except Exception as e:
        return {"error": str(e)}

# Fraudulent transactions grouped by type in date range
@router.get("/quarterly_transactions/")
def get_quarterly_transactions(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1]))

    query = text("""
        SELECT type, COUNT(type)
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date AND is_fraud = '1'
        GROUP BY type;
    """)
    try:
        rows = db.execute(query, {"start_date": start.date(), "end_date": end.date()}).fetchall()
        return {
            "start_date": start.date(),
            "end_date": end.date(),
            "labels": [row[0] for row in rows],
            "series": [row[1] for row in rows]
        }
    except Exception as e:
        return {"error": str(e)}

# Top high-risk users based on fraud probability
@router.get("/top_high_risk_users/")
def get_top_high_risk_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1]))

    query = text("""
        SELECT "nameDest", MAX(fraud_probability) AS max_fraud_prob
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '1' AND fraud_probability IS NOT NULL
        GROUP BY "nameDest"
        ORDER BY max_fraud_prob DESC
        LIMIT :limit;
    """)
    try:
        rows = db.execute(query, {"start_date": start.date(), "end_date": end.date(), "limit": limit}).fetchall()
        return {
            "start_date": start.date(),
            "end_date": end.date(),
            "users": [{"name": row[0], "risk_score": float(row[1])} for row in rows]
        }
    except Exception as e:
        return {"error": str(e)}

# Detailed view of high-risk transactions
@router.get("/detail_high_risk_users/")
def get_detail_top_high_risk_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1]))

    query = text("""
        SELECT trxdate, "nameOrig", type, amount, "nameDest", fraud_probability
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '1' AND fraud_probability IS NOT NULL
        ORDER BY trxdate DESC
        LIMIT :limit;
    """)
    try:
        rows = db.execute(query, {"start_date": start.date(), "end_date": end.date(), "limit": limit}).fetchall()
        return {
            "data": [
                {
                    "trxdate": row[0].strftime('%Y-%m-%d'),
                    "nameOrig": row[1],
                    "type": row[2],
                    "amount": float(row[3]),
                    "nameDest": row[4],
                    "fraud_probability": float(row[5])
                } for row in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# Map of suspicious locations
@router.get("/suspicious_location/")
def get_locations_of_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(month=1, day=1), today)

    query = text("""
        SELECT latitude, longitude, fraud_probability
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '1'
        AND latitude IS NOT NULL AND longitude IS NOT NULL
        AND fraud_probability IS NOT NULL;
    """)
    try:
        rows = db.execute(query, {"start_date": start.date(), "end_date": end.date()}).fetchall()
        return {
            "data": [
                {"x": float(row[1]), "y": float(row[0]), "r": max(4, float(row[2]) * 10)}
                for row in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}
