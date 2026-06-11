import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

conn = psycopg.connect(
    os.getenv("POSTGRES_URL")
)