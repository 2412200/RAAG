import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()
DATABASE_URL = os.getenv("POSTGRES_URL")
pool = ConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=10, check=ConnectionPool.check_connection)

def get_pg_connection():
    return pool.connection()  # Trigger reload after env change
