from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import calendar
from database import get_db
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
import pandas as pd
from fpdf import FPDF
import os
from tempfile import NamedTemporaryFile


router = APIRouter(
    prefix="/suspicious",
    tags=["suspicious"]
)

# ----------------------------- #
#         Pydantic Models      #
# ----------------------------- #

class SuspiciousDayCount(BaseModel):
    day: str
    suspicious_count: int

class TransactionVolume(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    total_volume: float
    fraud_volume: float
    non_fraud_volume: float
    
class TransactionTypeCount(BaseModel):
    type: str
    count: int

class HighRiskUser(BaseModel):
    name: str
    risk_score: float

class HighRiskTransaction(BaseModel):
    trxdate: str
    nameOrig: str
    type: str
    amount: float
    nameDest: str
    fraud_probability: float

class SuspiciousLocation(BaseModel):
    x: float  # longitude
    y: float  # latitude
    r: float  # radius

# ----------------------------- #
#       Utility Functions       #
# ----------------------------- #

def default_start_end_dates(start_date: Optional[str], end_date: Optional[str], default_start: datetime, default_end: datetime) -> Tuple[datetime, datetime]:
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else default_start
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else default_end
        return start, end
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

def get_current_month_range() -> Tuple[datetime, datetime]:
    today = datetime.today()
    return today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1])

# ----------------------------- #
#           Endpoints           #
# ----------------------------- #

@router.get("/suspicious_transactions_by_day/", response_model=List[SuspiciousDayCount])
def suspicious_transactions_by_day(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

    query = text("""
        SELECT DATE(trxdate) AS day, COUNT(*) AS suspicious_count
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date AND is_fraud = '1'
        GROUP BY day ORDER BY day;
    """)

    result = db.execute(query, {"start_date": start.date(), "end_date": end.date()}).fetchall()
    return [{"day": str(row[0]), "suspicious_count": row[1]} for row in result]

@router.get("/transaction_volume/", response_model=List[TransactionVolume])
def get_transaction_volume(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(month=1, day=1), today)

    # Total volume
    total_query = text("""
        SELECT SUM(amount) FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date;
    """)
    total_result = db.execute(total_query, {"start_date": start.date(), "end_date": end.date()}).fetchone()
    total_volume = float(total_result[0]) if total_result[0] is not None else 0.0

    # Fraudulent volume
    fraud_query = text("""
        SELECT SUM(amount) FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '1';
    """)
    fraud_result = db.execute(fraud_query, {"start_date": start.date(), "end_date": end.date()}).fetchone()
    fraud_volume = float(fraud_result[0]) if fraud_result[0] is not None else 0.0

    # Non-fraudulent volume
    nonfraud_query = text("""
        SELECT SUM(amount) FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '0';
    """)
    nonfraud_result = db.execute(nonfraud_query, {"start_date": start.date(), "end_date": end.date()}).fetchone()
    nonfraud_volume = float(nonfraud_result[0]) if nonfraud_result[0] is not None else 0.0

    return [{
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "total_volume": total_volume,
        "fraud_volume": fraud_volume,
        "non_fraud_volume": nonfraud_volume
    }]



class TransactionTypeAmounts(BaseModel):
    type: str
    amounts: List[float]


@router.get("/mobile_network/")
def get_mobile_network(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    today = datetime.today()
    start, end = default_start_end_dates(start_date, end_date, today.replace(month=1, day=1), today)

    query = text("""
        SELECT mobilenetwork, COUNT(mobilenetwork)
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date AND is_fraud = '1'
        GROUP BY mobilenetwork;
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
        raise HTTPException(status_code=500, detail=f"Error fetching quarterly transactions: {str(e)}")

@router.get("/transaction_type_distribution/", response_model=List[TransactionTypeAmounts])
def get_transaction_type_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

    # Get all transaction amounts and their types in date range
    query = text("""
        SELECT type, amount
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
    """)
    try:
        rows = db.execute(query, {"start_date": start.date(), "end_date": end.date()}).fetchall()
        
        # Organize amounts by type
        amounts_by_type: Dict[str, List[float]] = {}
        for t, amt in rows:
            amounts_by_type.setdefault(t, []).append(float(amt))
        
        # Return in the shape matching response model
        return [{"type": k, "amounts": v} for k, v in amounts_by_type.items()]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching type distribution: {str(e)}")



@router.get("/quarterly_transactions/")
def get_quarterly_transactions(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

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
        raise HTTPException(status_code=500, detail=f"Error fetching quarterly transactions: {str(e)}")

@router.get("/top_high_risk_users/", response_model=Dict[str, Any])
def get_top_high_risk_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

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
        raise HTTPException(status_code=500, detail=f"Error fetching high-risk users: {str(e)}")

@router.get("/detail_high_risk_users/", response_model=Dict[str, List[HighRiskTransaction]])
def get_detail_top_high_risk_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, gt=0),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

    query = text("""
        SELECT trxdate, "nameOrig", type, amount, "nameDest", fraud_probability
        FROM transactiontbl
        WHERE trxdate::date BETWEEN :start_date AND :end_date
        AND is_fraud = '1' AND fraud_probability IS NOT NULL
        ORDER BY trxdate DESC
        LIMIT :limit OFFSET :offset;
    """)
    try:
        rows = db.execute(query, {
            "start_date": start.date(), "end_date": end.date(),
            "limit": limit, "offset": offset
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
        raise HTTPException(status_code=500, detail=f"Error fetching detailed transactions: {str(e)}")

@router.get("/suspicious_location/", response_model=Dict[str, List[SuspiciousLocation]])
def get_locations_of_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
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
                {"x": float(row[1]), "y": float(row[0]), "r": max(4.0, float(row[2]) * 10)}
                for row in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching suspicious locations: {str(e)}")


@router.get("/export/high_risk_users/excel", response_class=FileResponse)
def export_high_risk_users_excel(
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT trxdate, "nameOrig", "nameDest", amount, type, mobilenetwork, latitude, longitude, fraud_probability
        FROM transactiontbl
        WHERE is_fraud = '1'
        AND fraud_probability IS NOT NULL
        ORDER BY fraud_probability DESC;
    """)
    rows = db.execute(query).fetchall()
    df = pd.DataFrame(rows, columns=[
        "trxdate", "nameOrig", "nameDest", "amount", "type",
        "mobilenetwork", "latitude", "longitude", "fraud_probability"
    ])

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df.to_excel(tmp.name, index=False)
        tmp_path = tmp.name

    return FileResponse(
        path=tmp_path,
        filename="high_risk_users.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/monthly_fraud/", response_model=Dict[str, Any])
def get_monthly_fraud(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Determine the start and end date range
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

    # SQL query to count frauds grouped by month number
    query = text("""
        SELECT EXTRACT(MONTH FROM trxdate) AS month, COUNT(*) AS fraud_count
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date
          AND is_fraud = '1'
        GROUP BY month
        ORDER BY month;
    """)

    try:
        rows = db.execute(query, {
            "start_date": start.date(),
            "end_date": end.date()
        }).fetchall()

        return {
            "start_date": start.date(),
            "end_date": end.date(),
            "labels": [int(row[0]) for row in rows],   # Month numbers (1–12)
            "values": [row[1] for row in rows]         # Fraud counts per month
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly fraud transactions: {str(e)}")
        
@router.get("/api/daily_trend/", response_model=Dict[str, Any])
def get_daily_trend(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Get default date range
    start, end = default_start_end_dates(start_date, end_date, *get_current_month_range())

    # Query total transactions per day
    total_query = text("""
        SELECT DATE(trxdate) AS day, COUNT(*) AS count
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date
        GROUP BY day
        ORDER BY day;
    """)

    # Query fraud transactions per day
    fraud_query = text("""
        SELECT DATE(trxdate) AS day, COUNT(*) AS count
        FROM transactiontbl
        WHERE trxdate BETWEEN :start_date AND :end_date
          AND is_fraud = '1'
        GROUP BY day
        ORDER BY day;
    """)

    try:
        total_rows = db.execute(total_query, {
            "start_date": start.date(),
            "end_date": end.date()
        }).fetchall()

        fraud_rows = db.execute(fraud_query, {
            "start_date": start.date(),
            "end_date": end.date()
        }).fetchall()

        # Convert rows to dicts for quick lookup
        total_map = {row[0].day: row[1] for row in total_rows}
        fraud_map = {row[0].day: row[1] for row in fraud_rows}

        # Build full list of days in the range
        day_labels = list(range(1, (end - start).days + 2))  # +1 to include end day
        total_counts = [total_map.get(day, 0) for day in day_labels]
        fraud_counts = [fraud_map.get(day, 0) for day in day_labels]

        return {
            "start_date": start.date(),
            "end_date": end.date(),
            "labels": day_labels,
            "total_counts": total_counts,
            "fraud_counts": fraud_counts
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching daily transaction trend: {str(e)}"
        )


@router.get("/export/high_risk_users/pdf", response_class=FileResponse)
def export_high_risk_users_pdf(
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT trxdate, "nameOrig", "nameDest", amount, type, mobilenetwork, latitude, longitude, fraud_probability
        FROM transactiontbl
        WHERE is_fraud = '1'
        AND fraud_probability IS NOT NULL
        ORDER BY fraud_probability DESC;
    """)
    rows = db.execute(query).fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Top High-Risk Users", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(100, 10, "Name", border=1)
    pdf.cell(50, 10, "Fraud Score", border=1)
    pdf.ln()

    for row in rows:
        name = row[2]  # nameDest
        score = row[8]  # fraud_probability
        pdf.cell(100, 10, str(name), border=1)
        try:
            score_value = float(score)
            score_text = f"{score_value:.2f}"
        except (TypeError, ValueError):
            score_text = "N/A"
        pdf.cell(50, 10, score_text, border=1)
        pdf.ln()

    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp_path = tmp.name

    return FileResponse(
        path=tmp_path,
        filename="high_risk_users.pdf",
        media_type="application/pdf"
    )
