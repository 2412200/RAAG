import sys
import os
import asyncio
# Add the project root to python path so that 'backend' module can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from backend.helper.database import get_pg_connection
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import SETTINGS

username = quote_plus(SETTINGS.MONGO_USERNAME)
password = quote_plus(SETTINGS.MONGO_PASSWORD)
cluster = quote_plus(SETTINGS.MONGO_CLUSTER)

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
mongo_client = AsyncIOMotorClient(MONGO_URI)

# data from postgres
def postgres_conn():
    with get_pg_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM seller")
        seller_data = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]

        seller = pd.DataFrame(seller_data, columns=columns)

        cursor.close()

    return seller

#data from mongodb
async def mongodb_conn():
    
    database = mongo_client["Products"]
    collection = database["apparel"]
    product_data =await collection.find().to_list(length=None)
    product_df=pd.DataFrame(product_data)
    return product_df


postgres = postgres_conn()
mongo =asyncio.run(mongodb_conn())

data = pd.merge(
    postgres,
    mongo,
    left_on="phone",
    right_on="seller_phone",
    how="inner"
)

print(data.head())