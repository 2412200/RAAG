from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

username = quote_plus(os.getenv("MONGO_USERNAME"))
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster = quote_plus(os.getenv("MONGO_CLUSTER"))

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
client = AsyncIOMotorClient(MONGO_URI)
db = client["Products"]

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@router.get("/GET/seller/products")
async def get_seller_products(request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
    
    seller_phone = user.get("phone")
    
    collections = ["apparel", "fmcg", "mobile_accessories", "steel_work", "homeappliances", "pharma"]
    products = []
    
    for col_name in collections:
        col = db[col_name]
        cursor = col.find({"seller_phone": seller_phone})
        async for doc in cursor:
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            # Map collection name to specification name for consistency in UI
            spec_name = col_name
            if col_name == "homeappliances":
                spec_name = "home_appliances"
            elif col_name == "pharma":
                spec_name = "pharmacy"
            doc["specification"] = spec_name
            products.append(doc)
            
    return {"products": products}
