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
    
    orders_col = client["Orders"]["orders"]
    cursor = orders_col.find({"customer_number": buyer_number})
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
            
        buyer_orders.append(order_doc)
        
    buyer_orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)
    return {"orders": buyer_orders}


@router.get("/GET/product")
async def get_product_details(product_id: str, specification: str):
    from bson import ObjectId
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
        
    try:
        doc = await db[col_name].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        
        doc["_id"] = str(doc["_id"])
        return doc
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
    collections = ["apparel", "fmcg", "mobile_accessories", "steel_work", "homeappliances", "pharma"]
    seller_product_names = set()
    product_category_map = {}
    
    for col_name in collections:
        col = db[col_name]
        cursor = col.find({"seller_phone": seller_phone}, {"product_name": 1, "name": 1})
        async for doc in cursor:
            name = doc.get("product_name") or doc.get("name")
            if name:
                seller_product_names.add(name)
                product_category_map[name] = col_name.replace("_", " ").title()
                
    # Fetch all orders to aggregate stats
    orders_col = client["Orders"]["orders"]
    cursor = orders_col.find({})
    
    total_revenue = 0.0
    total_orders_count = 0
    completed_orders_count = 0
    category_sales = {}
    product_sales_qty = {}
    product_sales_rev = {}
    
    async for order_doc in cursor:
        order_status = order_doc.get("order_status", "Pending")
        order_products = order_doc.get("products", [])
        
        has_seller_item = False
        order_subtotal = 0.0
        
        for item in order_products:
            p_name = item.get("product_name")
            if p_name in seller_product_names:
                has_seller_item = True
                qty = item.get("quantity", 0)
                price = item.get("price", 0.0)
                item_total = qty * price
                order_subtotal += item_total
                
                product_sales_qty[p_name] = product_sales_qty.get(p_name, 0) + qty
                product_sales_rev[p_name] = product_sales_rev.get(p_name, 0.0) + item_total
                
                cat = product_category_map.get(p_name, "Other")
                category_sales[cat] = category_sales.get(cat, 0.0) + item_total
                
        if has_seller_item:
            total_orders_count += 1
            if order_status in ["Completed", "Delivered", "Processing", "Shipped"]:
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


