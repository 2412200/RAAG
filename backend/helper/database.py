import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")

def get_pg_connection():
    return psycopg.connect(DATABASE_URL)