from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from backend.database import get_connection

router = APIRouter()

# GET request for all warehouses
@router.get("/GET/warehouses")
def get_warehouses():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Warehouses limit 5')
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    data = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return data

# GET request for warehouse by warehouse id
@router.get("/GET/warehouses/{warehouse_id}")
def get_warehouse(warehouse_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM Warehouses WHERE Warehouseid = %s',
        (warehouse_id,)
    )

    row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    columns = [desc[0] for desc in cursor.description]
    data = dict(zip(columns, row))

    cursor.close()
    conn.close()

    return data