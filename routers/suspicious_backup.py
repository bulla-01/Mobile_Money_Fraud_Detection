from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime
from database import get_db
import calendar

router = APIRouter(
    prefix="/suspicious",
    tags=["suspicious"]
)

def default_start_end_dates(start_date: Optional[str], end_date: Optional[str], default_start: datetime, default_end: datetime):
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else default_start
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else default_end
    return start, end

@router.get("/suspicious_transactions_by_day/", response_model=List[Dict])
def suspicious_transactions_by_day(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    today = datetime.today()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    start, end = default_start_end_dates(start_date, end_date, start_of_month, end_of_month)

    query = text("""
        SELECT DATE(trxdate) AS day, COUNT(*) AS suspicious_count
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date AND is_fraud = '1'
        GROUP BY day ORDER BY day;
    """)

    try:
        result = db.execute(query, {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d')
        }).fetchall()

        return [{"day": str(row[0]), "suspicious_count": row[1]} for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transaction_volume/", response_model=List[Dict])
def get_transaction_volume(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    today = datetime.today()
    default_start = today.replace(month=1, day=1).strftime('%Y-%m-%d')
    default_end = today.strftime('%Y-%m-%d')
    start = start_date if start_date else default_start
    end = end_date if end_date else default_end

    query = text("""
        SELECT SUM(amount) FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date AND is_fraud = '1';
    """)

    try:
        result = db.execute(query, {"start_date": start, "end_date": end}).fetchall()
        volume = float(result[0][0]) if result[0][0] is not None else 0.0
        return [{"from": start, "to": end, "volume": volume}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transaction_type_distribution/")
def get_transaction_type_distribution(db: Session = Depends(get_db)):
    query = text("""
        SELECT type, COUNT(*) FROM transactiontbl GROUP BY type
    """)
    try:
        result = db.execute(query).fetchall()
        return {"data": [{"type": row[0], "count": row[1]} for row in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quarterly_transactions/")
def get_quarterly_transactions(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    start, end = default_start_end_dates(start_date, end_date, start_of_month, end_of_month)

    query = text("""
        SELECT type, COUNT(type)
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date AND is_fraud = '1'
        GROUP BY type;
    """)
    try:
        rows = db.execute(query, {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d')
        }).fetchall()
        return {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d'),
            "labels": [row[0] for row in rows],
            "series": [row[1] for row in rows]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top_high_risk_users/")
def get_top_high_risk_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    start, end = default_start_end_dates(start_date, end_date, start_of_month, end_of_month)

    query = text("""
        SELECT "nameDest", MAX(fraud_probability) AS max_fraud_prob
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
          AND LOWER(is_fraud) = '1' AND fraud_probability IS NOT NULL
        GROUP BY "nameDest"
        ORDER BY max_fraud_prob DESC
        LIMIT :limit
    """)
    try:
        rows = db.execute(query, {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d'),
            "limit": limit
        }).fetchall()
        return {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d'),
            "users": [{"name": row[0], "risk_score": row[1]} for row in rows]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detail_high_risk_users/")
def get_detail_top_high_risk_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    start, end = default_start_end_dates(start_date, end_date, start_of_month, end_of_month)

    query = text("""
        SELECT trxdate, "nameOrig", type, amount, "nameDest", fraud_probability
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
          AND is_fraud = '1' AND fraud_probability IS NOT NULL
        ORDER BY trxdate DESC
        LIMIT :limit
    """)
    try:
        rows = db.execute(query, {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d'),
            "limit": limit
        }).fetchall()
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suspicious_location/")
def get_locations_of_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = datetime.today()
    start_of_year = today.replace(month=1, day=1)
    end_of_today = today
    start, end = default_start_end_dates(start_date, end_date, start_of_year, end_of_today)

    query = text("""
        SELECT latitude, longitude, fraud_probability
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
          AND is_fraud = '1'
          AND latitude IS NOT NULL AND longitude IS NOT NULL
          AND fraud_probability IS NOT NULL
    """)
    try:
        rows = db.execute(query, {
            "start_date": start.strftime('%Y-%m-%d'),
            "end_date": end.strftime('%Y-%m-%d')
        }).fetchall()
        return {
            "data": [
                {"x": float(row[1]), "y": float(row[0]), "r": max(4, float(row[2]) * 10)}
                for row in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
