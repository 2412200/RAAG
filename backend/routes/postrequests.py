from backend.database import get_connection
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from backend.pydanticmodels import ModelWarehouse

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