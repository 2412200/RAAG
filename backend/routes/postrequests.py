from backend.database import get_connection
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from backend.pydanticmodels import  Order_items, SignupRequest, LoginRequest, apparel, fmcg, mobile_accessories, steel_work
from datetime import date
from fastapi import Form, UploadFile, File
from backend.database import get_connection, get_users_connection
from passlib.context import CryptContext
from pydantic import BaseModel
from backend.database import add_product
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request

load_dotenv()

router = APIRouter()

username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
cluster = os.getenv("MONGO_CLUSTER")

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URI)

db = client["Products"]


@router.post("/POST/order_items")
def order_items(order_items : Order_items):
    for i in order_items.itemname:
        print(i)
    for i in order_items.quantity:
        print(i)
    return "hello"

@router.post("/POST/signup")
def signup(data: SignupRequest):
    conn = None
    cursor = None
    try:
        conn = get_users_connection()
        cursor = conn.cursor()

        table = "manufacturer" if data.role == "manufacturer" else "retailer"

        cursor.execute(f"SELECT 1 FROM {table} WHERE phone = %s", (data.phone,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Phone number already exists.")

        cursor.execute(
            f"""INSERT INTO {table} (company_name, phone, address, password_) 
            VALUES (%s, %s, %s, %s)""",
            (data.company, data.phone, data.address, data.password)
        )
        conn.commit()
        return {"message": "Account created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.post("/POST/login")
def login(data: LoginRequest):
    conn = None
    cursor = None
    try:
        conn = get_users_connection()
        cursor = conn.cursor()

        table = "manufacturer" if data.role == "manufacturer" else "retailer"

        cursor.execute(
    f"SELECT id FROM {table} WHERE phone = %s AND password_ = %s",
    (data.phone, data.password)
)
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        return {"message": "Login successful", "role": data.role}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.post("/POST/product")
async def add_product(request : Request):
    form = await request.form()

    product_specification = form.get("specification")

    if product_specification == "apparel":

        apparel_product = apparel(
            product_name=form.get("product_name"),
            size=form.get("size"),
            fabric=form.get("fabric"),
            category=form.get("category"),
            gsm=form.get("gsm"),
            mrp=form.get("mrp"),
            gender=form.get("gender")
        )

        result = await db["apparel"].insert_one(
            apparel_product.model_dump()
        )

        return {
            "message": "Apparel product added",
            "id": str(result.inserted_id)
        }

    elif product_specification == "fmcg":

        fmcg_product = fmcg(
            product_name=form.get("product_name"),
            brand=form.get("brand"),
            category= form.get("category"),
            quantity = form.get("quantity"),
            mrp = form.get("mrp"),
            manufacturing_date = form.get("manufacturing_date"),
            expiry_date = form.get("expiry_date"),
        )

        result = await db["fmcg"].insert_one(
            fmcg_product.model_dump()
        )

        return {
            "message": "FMCG product added",
            "id": str(result.inserted_id)
        }
    
    elif product_specification == "mobile_accessories":
        ma_product = mobile_accessories(
            product_name = form.get("product_name"),
            brand = form.get("brand"),
            compatible_model = form.get("compatible_model"),
            accessory_type = form.get("accessory_type"),
            color = form.get("color"),
            warranty = form.get("warranty"),
            mrp = form.get("mrp")
        )
        result = await db["mobile_accessories"].insert_one(
            ma_product.model_dump()
        )

        return {
            "message": "Mobile product added",
            "id": str(result.inserted_id)
        }
    
    elif product_specification == "steel_work":
        sw_product = steel_work(
            product_name = form.get("product_name"),
            steel_grade = form.get("steel_grade"),
            thickness = form.get("thickness"),
            weight = form.get("weight"),
            finish_type = form.get("finish_type"),
            mrp = form.get("mrp")
        )
        result = await db["steel_work"].insert_one(
            sw_product.model_dump()
        )

        return {
            "message": "Steel product added",
            "id": str(result.inserted_id)
        }


    raise HTTPException(
        status_code=400,
        detail="Invalid product specification"
    )
