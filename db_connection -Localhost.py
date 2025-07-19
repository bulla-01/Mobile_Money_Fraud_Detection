import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """
    Establishes and returns a new psycopg2 connection using DATABASE_URL from environment.
    """
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@db:5432/momo_db")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn
