from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from psycopg_pool import ConnectionPool
from backend.config import SETTINGS
import os

# Postgres connection pool
pool = ConnectionPool(
    conninfo=SETTINGS.POSTGRES_URL, 
    min_size=1, 
    max_size=10, 
    check=ConnectionPool.check_connection
)

def get_pg_connection():
    return pool.connection()

# MongoDB Client and Database Configuration
username = quote_plus(SETTINGS.MONGO_USERNAME)
password = quote_plus(SETTINGS.MONGO_PASSWORD)
cluster = quote_plus(SETTINGS.MONGO_CLUSTER)

if username and password and cluster:
    MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
else:
    MONGO_URI = os.getenv("MONGO_URI", "")

mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client["Products"]
# You can get any other db using mongo_client["DbName"]
