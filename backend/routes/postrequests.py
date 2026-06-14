from fastapi import HTTPException, APIRouter, Response
from fastapi.responses import JSONResponse
from backend.pydanticmodels import SignupRequest, LoginRequest, apparel, fmcg, mobile_accessories, steel_work, orders
from backend.helper.database import get_pg_connection
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request
from urllib.parse import quote_plus
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_please_change")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


load_dotenv()

router = APIRouter()

username = quote_plus(os.getenv("MONGO_USERNAME"))
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster = quote_plus(os.getenv("MONGO_CLUSTER"))

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URI)

db = client["Products"]

@router.post("/POST/signup")
def signup(data: SignupRequest):
    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        hashed_password = pwd_context.hash(data.password)

        if data.role == "manufacturer":

            cursor.execute("""
                INSERT INTO manufacturer
                (
                    company_name,
                    owner_name,
                    phone,
                    address,
                    password_
                )
                VALUES (%s,%s,%s,%s,%s)
            """, (
                data.business_name,
                data.owner_name,
                data.phone,
                data.address,
                hashed_password
            ))

        else:

            cursor.execute("""
                INSERT INTO retailer
                (
                    shop_name,
                    owner_name,
                    phone,
                    address,
                    password_
                )
                VALUES (%s,%s,%s,%s,%s)
            """, (
                data.business_name,
                data.owner_name,
                data.phone,
                data.address,
                hashed_password
            ))

        conn.commit()

        return {
            "message": "Account created"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.post("/POST/login")
def login(data: LoginRequest, response: Response):
    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        table = "manufacturer" if data.role == "manufacturer" else "retailer"

        cursor.execute(
            f"SELECT id, password_ FROM {table} WHERE phone = %s",
            (data.phone,)
        )
        user = cursor.fetchone()

        if not user or not pwd_context.verify(data.password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        token_data = {"phone": data.phone, "role": data.role}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True if using HTTPS in production
            samesite="lax",
            max_age=86400
        )

        return {"message": "Login successful", "role": data.role, "token": token}

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
        category=form.get("category"),
        quantity=form.get("quantity"),
        mrp=form.get("mrp"),
        manufacturing_date=form.get("manufacturing_date"),
        expiry_date=form.get("expiry_date"),
        )

        data = fmcg_product.model_dump()

        data["manufacturing_date"] = data["manufacturing_date"].isoformat()
        data["expiry_date"] = data["expiry_date"].isoformat()

        result = await db["fmcg"].insert_one(data)

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


@router.post("/POST/order")
async def post_order(order : orders):
    db = client["Orders"]
    result = await db["orders"].insert_one(order.model_dump())
    return {
        "message" : "Order placed successfully",
        "id" : str(result.inserted_id)
    }
    
