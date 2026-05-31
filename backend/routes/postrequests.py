from backend.database import get_connection
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from backend.pydanticmodels import ModelWarehouse, Orders, Order_items, apparels, SignupRequest, LoginRequest
from datetime import date
from fastapi import Form, UploadFile, File
import shutil, os
from backend.database import get_connection, get_users_connection
from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

@router.post("/POST/warehouses")
def post_warehouse(data: ModelWarehouse):

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM warehouses WHERE email = %s",
            (data.email,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Email already exists: {data.email}"
            )
        cursor.execute(
            "SELECT 1 FROM warehouses WHERE phone_number = %s",
            (data.phone_number,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Phone number already exists: {data.phone_number}"
            )
        query = """
        INSERT INTO warehouses
        (name,address,product,quantity,priceperpiece,phone_number,email,owner)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(query,(
            data.name,
            data.address,
            data.product,
            data.quantity,
            data.priceperpiece,
            data.phone_number,
            data.email,
            data.owner
        ))
        conn.commit()
        return {"message": "Data inserted successfully"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

from fastapi import HTTPException
from datetime import date

@router.post("/POST/orders")
def post_orders(orders: Orders):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT location FROM retailers WHERE retailer_id = %s",
            (orders.retailer_id,)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Retailer not found")

        (location,) = result

        cursor.execute(
            "SELECT warehouseid FROM warehouses WHERE warehouseid = %s",
            (orders.warehouseid,)
        )
        result2 = cursor.fetchone()

        if not result2:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        cursor.execute("""
            INSERT INTO orders (
                warehouseid,
                retailer_id,
                order_date,
                status,
                total_amount,
                shipping_address,
                payment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            orders.warehouseid,
            orders.retailer_id,
            date.today(),
            "Processing",
            0,
            location,
            "Not Done"
        ))

        conn.commit()

        return {"message": "Order created successfully"}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/POST/order_items")
def order_items(order_items : Order_items):
    for i in order_items.itemname:
        print(i)
    for i in order_items.quantity:
        print(i)
    return "hello"


@router.post("/POST/product")
async def add_product(
    productname: str = Form(...),
    size: str = Form(...),
    price: int = Form(...),
    fabric_name: str = Form(...),
    Category: str = Form(...),
    GSM: int = Form(...),
    Gender: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO apparels (productname, size, price, fabric, category, gsm, gender)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        productname,
        size,
        price,
        fabric_name,
        Category,
        GSM,
        Gender
    ))

    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Item Added successfully"}

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