from fastapi import HTTPException, APIRouter, Response
from fastapi.responses import JSONResponse
from backend.pydanticmodels import SignupRequest, LoginRequest, apparel, fmcg, mobile_accessories, steel_work, orders, ToggleVisibilityRequest, DeleteProductRequest, home_appliances, pharmacy
from backend.helper.database import get_pg_connection
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request
from urllib.parse import quote_plus
from jose import jwt
from passlib.context import CryptContext
import requests
from bson import ObjectId


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
    # Normalize phone number to E.164 format
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        # Check if user with this phone number already exists for this role
        table = "seller" if data.role == "seller" else "buyer"
        cursor.execute(f"SELECT 1 FROM {table} WHERE phone = %s", (data.phone,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f'user with {data.phone} already exists'
            )

        # Verify the OTP via Twilio VerificationCheck
        if not data.otp:
            raise HTTPException(
                status_code=400,
                detail="OTP is required to sign up"
            )

        twilio_check_url = f"https://verify.twilio.com/v2/Services/VA8615c88e13880d52c82e08acb4f51171/VerificationCheck"
        account_ssid = os.getenv("ACCOUNT_SID")
        auth_token = os.getenv("Twilio_auth_token")
        check_payload = {
            "To": data.phone,
            "Code": data.otp
        }
        response = requests.post(
            twilio_check_url,
            data=check_payload,
            auth=(account_ssid, auth_token)
        )
        if response.status_code != 200 or response.json().get("status") != "approved":
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP"
            )

        hashed_password = pwd_context.hash(data.password)

        if data.role == "seller":

            cursor.execute("""
                INSERT INTO seller
                (
                    company_name,
                    owner_name,
                    phone,
                    city,
                    state,
                    gst_pan,
                    category,
                    password_
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data.business_name,
                data.owner_name,
                data.phone,
                data.city,
                data.state,
                data.gst_pan,
                data.category,
                hashed_password
            ))

        else:

            cursor.execute("""
                INSERT INTO buyer
                (
                    shop_name,
                    owner_name,
                    phone,
                    city,
                    state,
                    category,
                    password_
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                data.business_name,
                data.owner_name,
                data.phone,
                data.city,
                data.state,
                data.category,
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
    # Normalize phone number to E.164 format
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        table = "seller" if data.role == "seller" else "buyer"

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

    user = getattr(request.state, "user", None)
    seller_phone = user.get("phone") if user else None
    
    # Fetch category from postgres
    seller_category = None
    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM seller WHERE phone = %s", (seller_phone,))
        row = cursor.fetchone()
        if row:
            seller_category = row[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database lookup failed: {str(e)}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    if not seller_category:
        raise HTTPException(status_code=400, detail="Seller category not found.")
        
    category_map = {
        "apparels": "apparel",
        "fmcg": "fmcg",
        "steel work": "steel_work",
        "home appliances": "home_appliances",
        "pharmacy": "pharmacy"
    }
    
    allowed_spec = category_map.get(seller_category)
    if product_specification != allowed_spec:
        raise HTTPException(
            status_code=400,
            detail=f"You can only add products matching your business category: {seller_category} (allowed: {allowed_spec})"
        )
        
    description = form.get("description", "")
    
    image_url = form.get("image_url", "")
    image_file = form.get("image_file")
    image_filename = None
    
    if image_file and hasattr(image_file, "filename") and image_file.filename:
        import uuid
        ext = os.path.splitext(image_file.filename)[1]
        image_filename = f"upload_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join("frontend/static/images", image_filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        contents = await image_file.read()
        with open(filepath, "wb") as f:
            f.write(contents)
    elif image_url:
        image_filename = image_url

    if product_specification == "apparel":

        apparel_product = apparel(
            product_name=form.get("product_name"),
            size=form.get("size"),
            fabric=form.get("fabric"),
            category=form.get("category"),
            gsm=form.get("gsm"),
            mrp=form.get("mrp"),
            gender=form.get("gender"),
            seller_phone=seller_phone,
            is_hidden=False,
            description=description,
            image=image_filename
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
            seller_phone=seller_phone,
            is_hidden=False,
            description=description,
            image=image_filename
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
            mrp = form.get("mrp"),
            seller_phone=seller_phone,
            is_hidden=False,
            description=description,
            image=image_filename
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
            mrp = form.get("mrp"),
            seller_phone=seller_phone,
            is_hidden=False,
            description=description,
            image=image_filename
        )
        result = await db["steel_work"].insert_one(
            sw_product.model_dump()
        )

        return {
            "message": "Steel product added",
            "id": str(result.inserted_id)
        }

    elif product_specification == "home_appliances":
        ha_product = home_appliances(
            product_name=form.get("product_name"),
            brand=form.get("brand"),
            mrp=form.get("mrp"),
            warranty=form.get("warranty"),
            seller_phone=seller_phone,
            is_hidden=False,
            description=description,
            image=image_filename
        )
        result = await db["homeappliances"].insert_one(
            ha_product.model_dump()
        )
        return {
            "message": "Home Appliance product added",
            "id": str(result.inserted_id)
        }

    elif product_specification == "pharmacy":
        ph_product = pharmacy(
            product_name=form.get("product_name"),
            brand=form.get("brand"),
            category=form.get("category"),
            mrp=form.get("mrp"),
            expiry_date=form.get("expiry_date"),
            seller_phone=seller_phone,
            is_hidden=False,
            description=description,
            image=image_filename
        )
        data = ph_product.model_dump()
        data["expiry_date"] = data["expiry_date"].isoformat()
        
        result = await db["pharma"].insert_one(data)
        return {
            "message": "Pharmacy product added",
            "id": str(result.inserted_id)
        }

    raise HTTPException(
        status_code=400,
        detail="Invalid product specification"
    )

@router.post("/POST/seller/product/toggle-visibility")
async def toggle_visibility(data: ToggleVisibilityRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
        
    seller_phone = user.get("phone")
    
    specification_to_collection = {
        "apparel": "apparel",
        "fmcg": "fmcg",
        "mobile_accessories": "mobile_accessories",
        "steel_work": "steel_work",
        "home_appliances": "homeappliances",
        "pharmacy": "pharma"
    }
    
    col_name = specification_to_collection.get(data.specification)
    if not col_name:
        raise HTTPException(status_code=400, detail="Invalid product specification")
        
    try:
        result = await db[col_name].update_one(
            {"_id": ObjectId(data.product_id), "seller_phone": seller_phone},
            {"$set": {"is_hidden": data.is_hidden}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found or not owned by you.")
            
        status_str = "hidden" if data.is_hidden else "visible"
        return {"message": f"Product is now {status_str}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/POST/seller/product/delete")
async def delete_product(data: DeleteProductRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
        
    seller_phone = user.get("phone")
    
    specification_to_collection = {
        "apparel": "apparel",
        "fmcg": "fmcg",
        "mobile_accessories": "mobile_accessories",
        "steel_work": "steel_work",
        "home_appliances": "homeappliances",
        "pharmacy": "pharma"
    }
    
    col_name = specification_to_collection.get(data.specification)
    if not col_name:
        raise HTTPException(status_code=400, detail="Invalid product specification")
        
    try:
        result = await db[col_name].delete_one(
            {"_id": ObjectId(data.product_id), "seller_phone": seller_phone}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found or not owned by you.")
            
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/POST/order")
async def post_order(order: orders, request: Request):
    user = getattr(request.state, "user", None)
    if user and user.get("phone"):
        conn = None
        cursor = None
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT shop_name, phone FROM buyer WHERE phone = %s",
                (user["phone"],)
            )
            row = cursor.fetchone()
            if row:
                shop_name, phone_str = row
                order.customer_name = shop_name
                digits = "".join(filter(str.isdigit, phone_str))
                if digits:
                    order.customer_number = int(digits)
        except Exception as e:
            print("Postgres lookup error during order placement:", e)
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    db = client["Orders"]
    result = await db["orders"].insert_one(order.model_dump())
    return {
        "message" : "Order placed successfully",
        "id" : str(result.inserted_id)
    }
    
@router.post("/POST/request-otp")
async def request_otp(data: SignupRequest):
    # Normalize phone number to E.164 format
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    conn = None
    cursor = None
    try:
        table = "buyer" if data.role == "buyer" else "seller"
        
        conn =get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
                f"SELECT id FROM {table} WHERE phone = %s",
                (data.phone,)
            )
        response = cursor.fetchone()
        if response:
            raise HTTPException(
                status_code=400,
                detail=f'user with {data.phone} already exists'
            )
        else:
            twilio_url = f"https://verify.twilio.com/v2/Services/VA8615c88e13880d52c82e08acb4f51171/Verifications"
            account_sid = os.getenv("ACCOUNT_SID")
            auth_token = os.getenv("Twilio_auth_token")
            payload = {
                "To" : data.phone,
                "Channel" : "sms"
            }
            response = requests.post(twilio_url,
            data=payload,
            auth=(account_sid,auth_token))
            if response.status_code == 201:
                return {"message": "otp sent successfully"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"OTP dispatch failed: {response.text}"
                )
            
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    