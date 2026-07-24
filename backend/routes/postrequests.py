from fastapi import HTTPException, APIRouter, Response, UploadFile,Depends
from fastapi.responses import JSONResponse
from backend.pydanticmodels import SignupRequest, LoginRequest, apparel, fmcg, mobile_accessories, steel_work, orders, ToggleVisibilityRequest, DeleteProductRequest, home_appliances, pharmacy, ForgotPasswordOTPRequest, ResetPasswordRequest, otp_request,CreateOrderRequest, CreateRazorpayOrderRequest, VerifyPaymentRequest
from backend.helper.database import get_pg_connection, mongo_client as client, mongo_db as db
from anyio.to_thread import run_sync
import os
from fastapi import Request
from jose import jwt
from passlib.context import CryptContext
import requests
from bson import ObjectId
from typing import Any, cast
from datetime import datetime, date
from psycopg import sql
import cloudinary
import cloudinary.uploader
import cloudinary.api
from backend.config import SETTINGS
from pydantic import BaseModel as PydanticBaseModel
import razorpay
cloudinary.config(
    cloud_name=SETTINGS.CLOUDINARY_CLOUD_NAME,
    api_key=SETTINGS.CLOUDINARY_API_KEY,
    api_secret=SETTINGS.CLOUDINARY_API_SECRET,
    secure=True
)

razorpay_client = SETTINGS.razorpay_client

SECRET_KEY = SETTINGS.SECRET_KEY
ALGORITHM = SETTINGS.ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

@router.post("/POST/signup")
def signup(data: SignupRequest, response: Response):
    # Normalize phone number to E.164 format
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cursor:
                # Check if user with this phone number already exists for this role
                table = "seller" if data.role == "seller" else "buyer"
                cursor.execute(
                    sql.SQL("SELECT 1 FROM {} WHERE phone = %s").format(sql.Identifier(table)),
                    (data.phone,)
                )
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

                twilio_check_url = f"https://verify.twilio.com/v2/Services/{SETTINGS.TWILIO_VERIFY_SERVICE_SID}/VerificationCheck"
                account_ssid = SETTINGS.ACCOUNT_SID
                auth_token = SETTINGS.TWILIO_AUTH_TOKEN
                check_payload = {
                    "To": data.phone,
                    "Code": data.otp
                }
                twilio_response = requests.post(
                    twilio_check_url,
                    data=check_payload,
                    auth=(account_ssid, auth_token)
                )
                if twilio_response.status_code != 200 or twilio_response.json().get("status") != "approved":
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

                return {
                    "message": "Account created",
                    "role": data.role,
                    "token": token
                }
    except HTTPException:
        raise
    except Exception as e:
        print("Error during signup:", e)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@router.post("/POST/login")
def login(data: LoginRequest, response: Response):
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cursor:
                table = "seller" if data.role == "seller" else "buyer"

                cursor.execute(
                    sql.SQL("SELECT phone, password_ FROM {} WHERE phone = %s").format(sql.Identifier(table)),
                    (data.phone,)
                )
                user = cursor.fetchone()
                if not user :
                    raise HTTPException(status_code = 401,detail="User does not exists")

                if not pwd_context.verify(data.password, user[1]):
                    raise HTTPException(status_code=401, detail="Incorrect Password")

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
        print("Error during login:", e)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@router.post("/POST/product")
async def add_product(request : Request):
    form = await request.form()

    product_specification = form.get("specification")

    user = getattr(request.state, "user", None)
    if not user or not user.get("phone"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    seller_phone = user["phone"]
    
    # Fetch category from postgres
    def get_seller_category_sync(phone):
        with get_pg_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT category FROM seller WHERE phone = %s", (phone,))
                row = cursor.fetchone()
                return row[0] if row else None

    try:
        seller_category = await run_sync(get_seller_category_sync, seller_phone)
    except Exception as e:
        print("Database lookup error in add_product:", e)
        raise HTTPException(status_code=500, detail="Database lookup failed. Please try again.")
        
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
        
    def get_str(val: Any) -> str:
        return val if isinstance(val, str) else ""

    def get_int(val: Any) -> int:
        if isinstance(val, str) and val.strip().isdigit():
            return int(val)
        return 0

    def get_float(val: Any) -> float:
        if isinstance(val, str):
            try:
                return float(val)
            except ValueError:
                pass
        return 0.0

    def get_date(val: Any) -> date:
        if isinstance(val, str):
            try:
                return datetime.strptime(val.strip(), "%Y-%m-%d").date()
            except ValueError:
                pass
        return date.today()

    description = get_str(form.get("description", ""))
    main_category = get_str(form.get("main_category", ""))
    sub_category1 = get_str(form.get("sub_category1", ""))
    sub_category2 = get_str(form.get("sub_category2", ""))
    sub_category3 = get_str(form.get("sub_category3", ""))
    
    product_id = ObjectId()
    image_files = form.getlist("image_file")
    images_list = []
    
    if image_files:
        folder_name = f"products/{seller_phone.replace('+', '')}/{str(product_id)}"
        
        # 1. Read all files asynchronously & validate size and type
        file_contents = []
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        for file in image_files:
            if hasattr(file, "filename") and file.filename and hasattr(file, "read"):
                # Validate type
                content_type = getattr(file, "content_type", "")
                if content_type and content_type not in ALLOWED_MIME_TYPES:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid file type for '{file.filename}'. Only JPEG, PNG, and WebP images are allowed."
                    )
                
                contents = await file.read()
                
                # Validate size
                if len(contents) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File '{file.filename}' exceeds the maximum allowed size of 5MB."
                    )
                file_contents.append(contents)
        
        # 2. Define a helper function to upload a single image synchronously
        def upload_single_file(contents):
            response = cloudinary.uploader.upload(contents, folder=folder_name)
            return response.get("secure_url")

        # 3. Upload all files in parallel using worker threads
        import asyncio
        if file_contents:
            tasks = [run_sync(upload_single_file, contents) for contents in file_contents]
            urls = await asyncio.gather(*tasks)
            images_list = [url for url in urls if url]

        
    from pydantic import ValidationError 
    try:
        if product_specification == "apparel":

            apparel_product = apparel(
                product_name=get_str(form.get("product_name")),
                size=cast(Any, [str(x) for x in form.getlist("size")]),
                fabric=get_str(form.get("fabric")),
                category=cast(Any, get_str(form.get("category"))),
                gsm=get_int(form.get("gsm")) or 180,
                mrp=get_float(form.get("mrp")),
                gender=cast(Any, get_str(form.get("gender"))),
                moq=get_int(form.get("moq")),
                seller_phone=seller_phone,
                is_hidden=False,
                description=description,
                images=images_list,
                main_category=main_category,
                sub_category1=sub_category1,
                sub_category2=sub_category2,
                sub_category3=sub_category3
            )

            product_data = apparel_product.model_dump()
            product_data["_id"] = product_id
            product_data["specification"] = "apparel"

            result = await db["products"].insert_one(product_data)

            return {
                "message": "Apparel product added",
                "id": str(result.inserted_id)
            }

        elif product_specification == "fmcg":
            fmcg_product = fmcg(
                product_name=get_str(form.get("product_name")),
                brand=get_str(form.get("brand")),
                category=cast(Any, get_str(form.get("category"))),
                quantity=get_int(form.get("quantity")),
                mrp=get_float(form.get("mrp")),
                manufacturing_date=get_date(form.get("manufacturing_date")),
                expiry_date=get_date(form.get("expiry_date")),
                seller_phone=seller_phone,
                is_hidden=False,
                description=description,
                images=images_list,
                main_category=main_category,
                sub_category1=sub_category1,
                sub_category2=sub_category2,
                sub_category3=sub_category3
            )

            product_data = fmcg_product.model_dump()
            product_data["_id"] = product_id
            product_data["specification"] = "fmcg"
            product_data["manufacturing_date"] = product_data["manufacturing_date"].isoformat()
            product_data["expiry_date"] = product_data["expiry_date"].isoformat()

            result = await db["products"].insert_one(product_data)

            return {
                "message": "FMCG product added",
                "id": str(result.inserted_id)
            }
        
        elif product_specification == "mobile_accessories":
            ma_product = mobile_accessories(
                product_name = get_str(form.get("product_name")),
                brand = get_str(form.get("brand")),
                compatible_model = get_str(form.get("compatible_model")),
                accessory_type = cast(Any, get_str(form.get("accessory_type"))),
                color = get_str(form.get("color")),
                warranty = get_int(form.get("warranty")),
                mrp = get_float(form.get("mrp")),
                seller_phone=seller_phone,
                is_hidden=False,
                description=description,
                images=images_list,
                main_category=main_category,
                sub_category1=sub_category1,
                sub_category2=sub_category2,
                sub_category3=sub_category3
            )
            product_data = ma_product.model_dump()
            product_data["_id"] = product_id
            product_data["specification"] = "mobile_accessories"
            result = await db["products"].insert_one(product_data)

            return {
                "message": "Mobile product added",
                "id": str(result.inserted_id)
            }
        
        elif product_specification == "steel_work":
            sw_product = steel_work(
                product_name = get_str(form.get("product_name")),
                steel_grade = get_str(form.get("steel_grade")),
                thickness = get_float(form.get("thickness")),
                weight = get_float(form.get("weight")),
                finish_type = cast(Any, get_str(form.get("finish_type"))),
                mrp = get_float(form.get("mrp")),
                seller_phone=seller_phone,
                is_hidden=False,
                description=description,
                images=images_list,
                main_category=main_category,
                sub_category1=sub_category1,
                sub_category2=sub_category2,
                sub_category3=sub_category3
            )
            product_data = sw_product.model_dump()
            product_data["_id"] = product_id
            product_data["specification"] = "steel_work"
            result = await db["products"].insert_one(product_data)

            return {
                "message": "Steel product added",
                "id": str(result.inserted_id)
            }

        elif product_specification == "home_appliances":
            ha_product = home_appliances(
                product_name=get_str(form.get("product_name")),
                brand=get_str(form.get("brand")),
                mrp=get_float(form.get("mrp")),
                warranty=get_int(form.get("warranty")),
                seller_phone=seller_phone,
                is_hidden=False,
                description=description,
                images=images_list,
                main_category=main_category,
                sub_category1=sub_category1,
                sub_category2=sub_category2,
                sub_category3=sub_category3
            )
            product_data = ha_product.model_dump()
            product_data["_id"] = product_id
            product_data["specification"] = "home_appliances"
            result = await db["products"].insert_one(product_data)
            return {
                "message": "Home Appliance product added",
                "id": str(result.inserted_id)
            }

        elif product_specification == "pharmacy":
            ph_product = pharmacy(
                product_name=get_str(form.get("product_name")),
                brand=get_str(form.get("brand")),
                category=cast(Any, get_str(form.get("category"))),
                mrp=get_float(form.get("mrp")),
                expiry_date=get_date(form.get("expiry_date")),
                seller_phone=seller_phone,
                is_hidden=False,
                description=description,
                images=images_list,
                main_category=main_category,
                sub_category1=sub_category1,
                sub_category2=sub_category2,
                sub_category3=sub_category3
            )
            product_data = ph_product.model_dump()
            product_data["_id"] = product_id
            product_data["specification"] = "pharmacy"
            product_data["expiry_date"] = product_data["expiry_date"].isoformat()
            
            result = await db["products"].insert_one(product_data)
            return {
                "message": "Pharmacy product added",
                "id": str(result.inserted_id)
            }

        raise HTTPException(
            status_code=400,
            detail="Invalid product specification"
        )
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            error_messages.append(f"{loc}: {error['msg']}")
        raise HTTPException(status_code=400, detail="Validation failed: " + ", ".join(error_messages))

@router.post("/POST/seller/product/toggle-visibility")
async def toggle_visibility(data: ToggleVisibilityRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
        
    seller_phone = user.get("phone")
    
    try:
        query_conditions = []
        try:
            query_conditions.append({"_id": ObjectId(data.product_id)})
        except Exception:
            pass
        query_conditions.append({"_id": data.product_id})
        
        id_query = {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0]
        
        result = await db["products"].update_one(
            {
                "$and": [
                    id_query,
                    {
                        "$or": [
                            {"seller_phone": seller_phone},
                            {"seller_phone": {"$exists": False}},
                            {"seller_phone": None}
                        ]
                    }
                ]
            },
            {"$set": {"is_hidden": data.is_hidden}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found or not owned by you.")
            
        status_str = "hidden" if data.is_hidden else "visible"
        return {"message": f"Product is now {status_str}"}
    except Exception as e:
        print("Error toggling product visibility:", e)
        raise HTTPException(status_code=500, detail="Internal server error while updating product visibility.")

@router.post("/POST/seller/product/delete")
async def delete_product(data: DeleteProductRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
        
    seller_phone = user.get("phone")
    
    try:
        query_conditions = []
        try:
            query_conditions.append({"_id": ObjectId(data.product_id)})
        except Exception:
            pass
        query_conditions.append({"_id": data.product_id})
        
        id_query = {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0]

        result = await db["products"].delete_one(
            {
                "$and": [
                    id_query,
                    {
                        "$or": [
                            {"seller_phone": seller_phone},
                            {"seller_phone": {"$exists": False}},
                            {"seller_phone": None}
                        ]
                    }
                ]
            }
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found or not owned by you.")
            
        return {"message": "Product deleted successfully"}
    except Exception as e:
        print("Error deleting product:", e)
        raise HTTPException(status_code=500, detail="Internal server error while deleting product.")

@router.post("/POST/order")
async def post_order(order: orders, request: Request):
    user = getattr(request.state, "user", None)
    if user and user.get("phone"):
        def get_buyer_details_sync(phone):
            with get_pg_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT shop_name, phone FROM buyer WHERE phone = %s",
                        (phone,)
                    )
                    return cursor.fetchone()
        try:
            row = await run_sync(get_buyer_details_sync, user["phone"])
            if row:
                shop_name, phone_str = row
                order.customer_name = shop_name
                digits = "".join(filter(str.isdigit, phone_str))
                if digits:
                    order.customer_number = int(digits)
        except Exception as e:
            print("Postgres lookup error during order placement:", e)
            


    orders_db = client["Orders"]
    result = await orders_db["orders"].insert_one(order.model_dump())
    return {
        "message" : "Order placed successfully",
        "id" : str(result.inserted_id)
    }
    
@router.post("/POST/request-otp")
def request_otp(data: otp_request): 

    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    try:
        table = "buyer" if data.role == "buyer" else "seller"
        
        with get_pg_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SELECT id FROM {} WHERE phone = %s").format(sql.Identifier(table)),
                    (data.phone,)
                )
                response = cursor.fetchone()
                if response:
                    raise HTTPException(
                        status_code=400,
                        detail=f'user with {data.phone} already exists'
                    )
                else:
                    twilio_url = f"https://verify.twilio.com/v2/Services/{SETTINGS.TWILIO_VERIFY_SERVICE_SID}/Verifications"
                    account_sid = SETTINGS.ACCOUNT_SID
                    auth_token = SETTINGS.TWILIO_AUTH_TOKEN
                    payload = {
                        "To" : data.phone,
                        "Channel" : "sms"
                    }
                    response = requests.post(twilio_url,
                    data=payload,
                    auth=(account_sid, auth_token))
                    if response.status_code == 201:
                        return {"message": "otp sent successfully"}
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"OTP cannot be generated"
                        )
            
    except HTTPException:
        raise
    except Exception as e:
        print("Error requesting signup OTP:", e)
        raise HTTPException(status_code=500, detail="Internal server error. Could not request verification OTP.")
    
@router.post("/POST/order/update-status")
async def update_order_status(data: dict):
    order_id = data.get("order_id")
    new_status = data.get("status")
    if not order_id or not new_status:
        raise HTTPException(status_code=400, detail="Missing order_id or status")
    
    try:
        db = client["Orders"]
        result = await db["orders"].update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"order_status": new_status}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"message": f"Order status updated to {new_status}"}
    except HTTPException:
        raise
    except Exception as e:
        print("Error updating order status:", e)
        raise HTTPException(status_code=500, detail="Internal server error while updating order status.")

@router.post("/POST/request-forgot-password-otp")
def request_forgot_password_otp(data: ForgotPasswordOTPRequest):
    # Normalize phone number to E.164 format
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    try:
        table = "buyer" if data.role == "buyer" else "seller"
        
        with get_pg_connection() as conn:
            with conn.cursor() as cursor:
                # Check if user with this phone number exists for this role
                cursor.execute(
                    sql.SQL("SELECT id FROM {} WHERE phone = %s").format(sql.Identifier(table)),
                    (data.phone,)
                )
                response = cursor.fetchone()
                if not response:
                    raise HTTPException(
                        status_code=404,
                        detail=f"User with phone number {data.phone} and role '{data.role}' not found"
                    )
                else:
                    twilio_url = f"https://verify.twilio.com/v2/Services/{SETTINGS.TWILIO_VERIFY_SERVICE_SID}/Verifications"
                    account_sid = SETTINGS.ACCOUNT_SID
                    auth_token = SETTINGS.TWILIO_AUTH_TOKEN
                    payload = {
                        "To" : data.phone,
                        "Channel" : "sms"
                    }
                    res = requests.post(twilio_url,
                                        data=payload,
                                        auth=(account_sid, auth_token))
                    if res.status_code == 201:
                        return {"message": "Verification code sent successfully"}
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Verification code cannot be generated"
                        )
            
    except HTTPException:
        raise
    except Exception as e:
        print("Error requesting password reset OTP:", e)
        raise HTTPException(status_code=500, detail="Internal server error while requesting verification code.")


@router.post("/POST/reset-password")
def reset_password(data: ResetPasswordRequest):
    # Normalize phone number to E.164 format
    phone_num = data.phone.strip().replace(" ", "")
    if not phone_num.startswith("+"):
        if len(phone_num) == 10:
            phone_num = "+91" + phone_num
        else:
            phone_num = "+" + phone_num
    data.phone = phone_num

    try:
        table = "buyer" if data.role == "buyer" else "seller"
        
        with get_pg_connection() as conn:
            with conn.cursor() as cursor:
                # Verify user exists
                cursor.execute(
                    sql.SQL("SELECT id FROM {} WHERE phone = %s").format(sql.Identifier(table)),
                    (data.phone,)
                )
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail="User not found"
                    )

                # Verify OTP with Twilio
                twilio_check_url = f"https://verify.twilio.com/v2/Services/{SETTINGS.TWILIO_VERIFY_SERVICE_SID}/VerificationCheck"
                account_ssid = SETTINGS.ACCOUNT_SID
                auth_token = SETTINGS.TWILIO_AUTH_TOKEN
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
                        detail="Invalid or expired verification code"
                    )

                hashed_password = pwd_context.hash(data.password)

                cursor.execute(
                    sql.SQL("UPDATE {} SET password_ = %s WHERE phone = %s").format(sql.Identifier(table)),
                    (hashed_password, data.phone)
                )
                conn.commit()

                return {
                    "message": "Password reset successfully"
                }

    except HTTPException:
        raise
    except Exception as e:
        print("Error resetting password:", e)
        raise HTTPException(status_code=500, detail="Internal server error while resetting password.")

class ProfileUpdateRequest(PydanticBaseModel):
    business_name: str
    owner_name: str
    city: str
    state: str

@router.post("/POST/user/update-profile")
async def update_profile(data: ProfileUpdateRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    phone = user.get("phone")
    role = user.get("role")
    table = "seller" if role == "seller" else "buyer"
    
    try:
        def update_pg_profile(phone_num, role_str):
            with get_pg_connection() as conn:
                with conn.cursor() as cursor:
                    if role_str == "seller":
                        cursor.execute("""
                            UPDATE seller
                            SET company_name = %s, owner_name = %s, city = %s, state = %s
                            WHERE phone = %s
                        """, (data.business_name, data.owner_name, data.city, data.state, phone_num))
                    else:
                        cursor.execute("""
                            UPDATE buyer
                            SET shop_name = %s, owner_name = %s, city = %s, state = %s
                            WHERE phone = %s
                        """, (data.business_name, data.owner_name, data.city, data.state, phone_num))
                    conn.commit()
                    
        await run_sync(update_pg_profile, phone, role)
        return {"message": "Profile updated successfully"}
    except Exception as e:
        print("Error updating profile in PG:", e)
        raise HTTPException(status_code=500, detail="Database error while updating profile.")


@router.post("/POST/seller/product/edit")
async def edit_product(request: Request):
    form = await request.form()
    product_id = form.get("product_id")
    specification = form.get("specification")
    
    if not product_id or not specification or not isinstance(product_id, str) or not isinstance(specification, str):
        raise HTTPException(status_code=400, detail="Missing product_id or specification")
        
    user = getattr(request.state, "user", None)
    if not user or not user.get("phone") or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
        
    seller_phone: str = user["phone"]
    
    specification_to_collection = {
        "apparel": "apparel",
        "fmcg": "fmcg",
        "mobile_accessories": "mobile_accessories",
        "steel_work": "steel_work",
        "home_appliances": "homeappliances",
        "pharmacy": "pharma"
    }
    col_name = specification_to_collection.get(specification)
    if not col_name:
        raise HTTPException(status_code=400, detail="Invalid specification")
        
    existing = await db[col_name].find_one({"_id": ObjectId(product_id), "seller_phone": seller_phone})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
        
    update_fields = {}
    
    if "product_name" in form:
        p_name = form.get("product_name")
        if isinstance(p_name, str):
            update_fields["product_name"] = p_name
            update_fields["name"] = p_name
            
    if "mrp" in form:
        mrp_val = form.get("mrp")
        if isinstance(mrp_val, str):
            try:
                val = float(mrp_val)
                update_fields["mrp"] = val
                update_fields["price"] = val
            except ValueError:
                pass
                
    if "price" in form:
        price_val = form.get("price")
        if isinstance(price_val, str):
            try:
                val = float(price_val)
                update_fields["price"] = val
                update_fields["mrp"] = val
            except ValueError:
                pass
                
    if "description" in form:
        desc_val = form.get("description")
        if isinstance(desc_val, str):
            update_fields["description"] = desc_val
            
    if "stock" in form:
        stock_val = form.get("stock")
        if isinstance(stock_val, str):
            try:
                update_fields["stock"] = int(stock_val)
            except ValueError:
                pass
                
    if "quantity" in form or "qty" in form:
        qty_val = form.get("quantity") or form.get("qty")
        if isinstance(qty_val, str):
            try:
                val = int(qty_val)
                update_fields["quantity"] = val
                update_fields["qty"] = val
            except ValueError:
                pass
            
    image_files = form.getlist("image_file")
    if image_files and hasattr(image_files[0], "filename") and image_files[0].filename:
        folder_name = f"products/{seller_phone.replace('+', '')}/{str(product_id)}"
        file_contents = []
        MAX_FILE_SIZE = 5 * 1024 * 1024
        ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        
        for file in image_files:
            if hasattr(file, "filename") and file.filename and hasattr(file, "read"):
                content_type = getattr(file, "content_type", "")
                if content_type and content_type not in ALLOWED_MIME_TYPES:
                    raise HTTPException(status_code=400, detail="Invalid image type")
                contents = await file.read()
                if len(contents) > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="File too large")
                file_contents.append(contents)
                
        def upload_single_file(contents):
            res = cloudinary.uploader.upload(contents, folder=folder_name)
            return res.get("secure_url")
            
        import asyncio
        if file_contents:
            tasks = [run_sync(upload_single_file, contents) for contents in file_contents]
            urls = await asyncio.gather(*tasks)
            images_list = [url for url in urls if url]
            if images_list:
                update_fields["images"] = images_list
                update_fields["image"] = images_list[0]
                
    if not update_fields:
        return {"message": "No updates applied"}
        
    await db[col_name].update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_fields}
    )
    return {"message": "Product updated successfully"}

@router.post("/create-razorpay-order")
async def create_razorpay_order(payload: CreateOrderRequest):

    # 1. Validate and convert the incoming order_id string to ObjectId
    try:
        mongo_id = ObjectId(payload.order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order_id")

    # 2. Fetch the order from MongoDB
    orders_collection = client["Orders"]["orders"]
    order = await orders_collection.find_one({"_id": mongo_id})

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 3. Guard against double payment
    if order.get("order_status") == "Completed":
        raise HTTPException(status_code=400, detail="Order already paid")

    # 4. Calculate total amount — sum from products if no stored total_amount field
    total_amount = order.get("total_amount")
    if total_amount is None:
        total_amount = sum(
            item["price"] * item["quantity"] for item in order.get("products", [])
        )

    if not total_amount or total_amount <= 0:
        raise HTTPException(status_code=400, detail="Order has no valid amount")

    total_amount_in_paise = int(total_amount * 100)

    # 5. Create the order on Razorpay's side
    try:
        razorpay_order = cast(Any, razorpay_client).order.create({
            "amount": total_amount_in_paise,
            "currency": "INR",
            "receipt": f"raag_order_{payload.order_id}",
            "payment_capture": 1
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")

    # 6. Save Razorpay's order_id back onto the same Mongo document
    await orders_collection.update_one(
        {"_id": mongo_id},
        {"$set": {"razorpay_order_id": razorpay_order["id"]}}
    )

    # 7. Return what the frontend Checkout needs
    return {
        "razorpay_order_id": razorpay_order["id"],
        "amount": total_amount_in_paise,
        "currency": "INR",
        "key": os.getenv("RAZORPAY_KEY_ID")
    }

@router.post("/api/create-order")
def create_order(payload: CreateRazorpayOrderRequest):
    if payload.amount < 100:
        raise HTTPException(status_code=400, detail="Amount must be at least 100 paise")
        
    try:
        data = {
            "amount": payload.amount,
            "currency": payload.currency,
            "receipt": payload.receipt or "",
            "payment_capture": 1
        }
        razorpay_order = cast(Any, razorpay_client).order.create(data)
        return {
            "order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "key": SETTINGS.RAZORPAY_KEY_ID
        }
    except Exception as e:
        err_str = str(e).lower()
        if "auth" in err_str or "unauthorized" in err_str or "api key" in err_str or "credentials" in err_str:
            raise HTTPException(status_code=401, detail="Razorpay authentication failed")
        raise HTTPException(status_code=500, detail=f"Razorpay error: {str(e)}")

@router.post("/api/verify-payment")
def verify_payment(payload: VerifyPaymentRequest):
    if not payload.razorpay_order_id or not payload.razorpay_payment_id or not payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing required signature verification fields")
        
    import hmac
    import hashlib
    
    msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    generated_sig = hmac.new(
        SETTINGS.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(generated_sig, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment verification failed: Signature mismatch")
        
    return {"status": "success", "message": "Payment verified successfully"}