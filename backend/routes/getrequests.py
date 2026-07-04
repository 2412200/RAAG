from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from backend.helper.database import mongo_client as client, mongo_db as db

router = APIRouter()

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


@router.get("/GET/seller/orders")
async def get_seller_orders(request: Request):
    from datetime import datetime
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
    
    seller_phone = user.get("phone")
    
    # 1. Get all products of this seller to compile a list of their product names
    collections = ["apparel", "fmcg", "mobile_accessories", "steel_work", "homeappliances", "pharma"]
    seller_product_names = set()
    
    for col_name in collections:
        col = db[col_name]
        cursor = col.find({"seller_phone": seller_phone}, {"product_name": 1, "name": 1})
        async for doc in cursor:
            name = doc.get("product_name") or doc.get("name")
            if name:
                seller_product_names.add(name)
    
    # 2. Fetch all orders
    orders_col = client["Orders"]["orders"]
    cursor = orders_col.find({})
    seller_orders = []
    
    async for order_doc in cursor:
        matching_items = []
        order_products = order_doc.get("products", [])
        for item in order_products:
            p_name = item.get("product_name")
            if p_name in seller_product_names:
                matching_items.append({
                    "product_name": p_name,
                    "quantity": item.get("quantity"),
                    "price": item.get("price")
                })
        
        if matching_items:
            subtotal = sum(x["quantity"] * x["price"] for x in matching_items)
            created_at = order_doc.get("created_at")
            if isinstance(created_at, datetime):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                created_at_str = str(created_at) if created_at else ""
                
            seller_orders.append({
                "order_id": str(order_doc["_id"]),
                "customer_name": order_doc.get("customer_name"),
                "customer_number": order_doc.get("customer_number"),
                "created_at": created_at_str,
                "order_status": order_doc.get("order_status", "Pending"),
                "products": matching_items,
                "total_amount": subtotal
            })
            
    # Sort orders by created_at string descending
    seller_orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)
    return {"orders": seller_orders}

