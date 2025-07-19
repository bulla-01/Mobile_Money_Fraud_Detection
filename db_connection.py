import os
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """
    Establishes and returns a new psycopg2 connection using DATABASE_URL from .env.
    Ensures sslmode=require is included.
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL not found in environment variables")

    # Append sslmode=require if not already present
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    elif "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"

    try:
        conn = connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise ConnectionError(f"❌ Failed to connect to the database: {e}")
