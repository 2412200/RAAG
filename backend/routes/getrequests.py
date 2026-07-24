# backend/routes/getrequests.py - Handles GET requests for seller products, seller orders, buyer orders, and seller analytics.
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
    products = []
    
    cursor = db["products"].find({
        "$or": [
            {"seller_phone": seller_phone},
            {"seller_phone": {"$exists": False}},
            {"seller_phone": None}
        ]
    })
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
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
    seller_product_names = set()
    cursor = db["products"].find({"seller_phone": seller_phone}, {"product_name": 1, "name": 1})
    async for doc in cursor:
        name = doc.get("product_name") or doc.get("name")
        if name:
            seller_product_names.add(name)
    
    # 2. Fetch all orders
    orders_col = client["Orders"]["orders"]
    cursor = orders_col.find({"order_status": {"$ne": "Pending Payment"}})
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

@router.get("/GET/buyer/orders")
async def get_buyer_orders(request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "buyer":
        raise HTTPException(status_code=403, detail="Access denied. Buyers only.")
    
    phone_str = user.get("phone")
    if not phone_str:
        return {"orders": []}
    
    digits = "".join(filter(str.isdigit, phone_str))
    if not digits:
        return {"orders": []}
    
    buyer_number = int(digits)
    
    # Create product name-to-info mapping from catalog
    product_name_to_info = {}
    cursor_prod = db["products"].find({}, {"product_name": 1, "name": 1, "images": 1, "image": 1, "specification": 1})
    async for doc in cursor_prod:
        name = doc.get("product_name") or doc.get("name")
        if name:
            images = doc.get("images")
            image_val = images[0] if images and isinstance(images, list) and images else doc.get("image") or ""
            product_name_to_info[name] = {
                "id": str(doc["_id"]),
                "image": image_val,
                "specification": doc.get("specification", "apparel")
            }

    orders_col = client["Orders"]["orders"]
    cursor = orders_col.find({
        "customer_number": buyer_number,
        "order_status": {"$ne": "Pending Payment"}
    })
    buyer_orders = []
    
    from datetime import datetime
    async for order_doc in cursor:
        order_doc["_id"] = str(order_doc["_id"])
        created_at = order_doc.get("created_at")
        if isinstance(created_at, datetime):
            order_doc["created_at"] = created_at.strftime("%Y-%m-%d %H:%M")
        elif created_at:
            order_doc["created_at"] = str(created_at)
        else:
            order_doc["created_at"] = ""
            
        # Enrich each product item in the order with its resolved product_id, image, and spec
        for prod in order_doc.get("products", []):
            p_name = prod.get("product_name")
            info = product_name_to_info.get(p_name, {})
            prod["product_id"] = info.get("id", "N/A")
            prod["image"] = info.get("image", "default.webp")
            prod["specification"] = info.get("specification", "")
            
        buyer_orders.append(order_doc)
        
    buyer_orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)
    return {"orders": buyer_orders}


@router.get("/GET/product")
async def get_product_details(product_id: str, specification: str = None):
    from bson import ObjectId
    try:
        query_conditions = []
        try:
            query_conditions.append({"_id": ObjectId(product_id)})
        except Exception:
            pass
        query_conditions.append({"_id": product_id})
        
        query = {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0]
        
        doc = await db["products"].find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
                
        raise HTTPException(status_code=404, detail="Product not found")
    except HTTPException:
        raise
    except Exception as e:
        print("Error fetching product details:", e)
        raise HTTPException(status_code=500, detail="Error fetching product details")


@router.get("/GET/seller/analytics")
async def get_seller_analytics(request: Request):
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Access denied. Sellers only.")
        
    seller_phone = user.get("phone")
    
    # Get all products of this seller
    seller_product_names = set()
    product_category_map = {}
    
    cursor = db["products"].find({"seller_phone": seller_phone}, {"product_name": 1, "name": 1, "category": 1, "main_category": 1})
    async for doc in cursor:
        name = doc.get("product_name") or doc.get("name")
        if name:
            seller_product_names.add(name)
            cat = doc.get("main_category") or doc.get("category") or "Other"
            product_category_map[name] = cat

    # Fetch all orders to compute stats
    orders_col = client["Orders"]["orders"]
    cursor = orders_col.find({"order_status": {"$ne": "Pending Payment"}})
    
    total_revenue = 0.0
    total_orders_count = 0
    completed_orders_count = 0
    
    product_sales_qty = {}
    product_sales_rev = {}
    category_sales = {}
    
    async for order_doc in cursor:
        order_status = order_doc.get("order_status", "Pending")
        order_products = order_doc.get("products", [])
        has_seller_item = False
        order_subtotal = 0.0
        
        for item in order_products:
            p_name = item.get("product_name")
            if p_name in seller_product_names:
                has_seller_item = True
                qty = item.get("quantity", 1)
                price = item.get("price", 0.0)
                item_total = qty * price
                order_subtotal += item_total
                
                product_sales_qty[p_name] = product_sales_qty.get(p_name, 0) + qty
                product_sales_rev[p_name] = product_sales_rev.get(p_name, 0.0) + item_total
                
                cat = product_category_map.get(p_name, "Other")
                category_sales[cat] = category_sales.get(cat, 0.0) + item_total
                
        if has_seller_item:
            total_orders_count += 1
            if order_status.lower() in ["completed", "delivered"]:
                total_revenue += order_subtotal
                completed_orders_count += 1
                
    top_products = []
    for name, qty in product_sales_qty.items():
        top_products.append({
            "name": name,
            "quantity": qty,
            "revenue": product_sales_rev.get(name, 0.0),
            "category": product_category_map.get(name, "Other")
        })
    top_products.sort(key=lambda x: x["revenue"], reverse=True)
    
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders_count,
        "completed_orders": completed_orders_count,
        "category_sales": [{"category": k, "revenue": v} for k, v in category_sales.items()],
        "top_products": top_products[:5]
    }


@router.get("/GET/categories")
async def get_categories():
    import json
    import os
    try:
        json_path = os.path.join(os.getcwd(), "categories.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        return {"category": {}}
    except Exception as e:
        print("Error loading categories.json:", e)
        return {"category": {}}


