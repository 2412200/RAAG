from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes import getrequests, postrequests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from jose import jwt, JWTError
from backend.config import SETTINGS
from backend.helper.database import mongo_db as db

app = FastAPI()

app.include_router(getrequests.router)
app.include_router(postrequests.router)
app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)

templates = Jinja2Templates(directory="frontend/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

SECRET_KEY = SETTINGS.SECRET_KEY
ALGORITHM = SETTINGS.ALGORITHM


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Paths that don't require authentication
    public_paths = [
        "/", "/signup", "/POST/login", "/POST/signup", "/logout", 
        "/POST/request-otp", "/forgot-password", "/POST/request-forgot-password-otp", 
        "/POST/reset-password", "/state-demo", "/empty", "/loading", 
        "/offline", "/no-result", "/success"
    ]
    
    if request.url.path in public_paths or request.url.path.startswith("/static"):
        # Redirect authenticated users away from Login and Signup pages
        if request.url.path in ["/", "/signup"] and request.method == "GET":
            token = request.cookies.get("access_token")
            if token:
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    role = payload.get("role")
                    if role == "seller":
                        return RedirectResponse(url="/seller", status_code=303)
                    elif role == "buyer":
                        return RedirectResponse(url="/home", status_code=303)
                except JWTError:
                    pass
        return await call_next(request)
        
    token = request.cookies.get("access_token")
    if not token:
        if request.method == "GET":
            return RedirectResponse(url="/", status_code=303)
        return JSONResponse(status_code=401, content={"detail": "Not authenticated. Please login."})
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Attach user data to request state for access in endpoints
        request.state.user = payload
        
        # Enforce role-based access control (RBAC)
        role = payload.get("role")
        path = request.url.path
        
        # Seller paths
        seller_paths = ["/seller", "/POST/product"]
        # Buyer paths
        buyer_paths = [
            "/home", "/orders", "/cart", "/search", "/womens", "/mens-wear", 
            "/homeappliances", "/beauty", "/books", "/groceries", "/pharma", "/kids", "/furniture",
            "/POST/order"
        ]
        
        is_buyer_details = path.endswith("/details") or path.endswith("/detail")
        
        if role == "buyer" and path in seller_paths:
            if request.method == "GET":
                return RedirectResponse(url="/home", status_code=303)
            return JSONResponse(status_code=403, content={"detail": "Access denied. Sellers only."})
            
        if role == "seller" and (path in buyer_paths or is_buyer_details):
            if request.method == "GET":
                return RedirectResponse(url="/seller", status_code=303)
            return JSONResponse(status_code=403, content={"detail": "Access denied. Buyers only."})
            
    except JWTError:
        if request.method == "GET":
            return RedirectResponse(url="/", status_code=303)
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token. Please login again."})
        
    return await call_next(request)


@app.get("/")
async def login_page(request : Request):
    return templates.TemplateResponse(request, "login.html",{"request" : request})

@app.get("/signup")
async def signup_page(request : Request):
    return templates.TemplateResponse(request, "signup.html",{"request" : request})

@app.get("/forgot-password")
async def forgot_password_page(request : Request):
    return templates.TemplateResponse(request, "forgot_password.html", {"request" : request})

@app.get("/state-demo")
async def state_demo_page(request: Request):
    return templates.TemplateResponse(request, "state_demo.html", {"request": request})

@app.get("/empty")
async def empty_state_page(request: Request):
    return templates.TemplateResponse(request, "empty.html", {"request": request})

@app.get("/loading")
async def loading_state_page(request: Request):
    return templates.TemplateResponse(request, "loading.html", {"request": request})

@app.get("/offline")
async def offline_state_page(request: Request):
    return templates.TemplateResponse(request, "offline.html", {"request": request})

@app.get("/no-result")
async def no_result_state_page(request: Request, q: str | None = None):
    return templates.TemplateResponse(request, "no_result.html", {"request": request, "query": q or "Mock Search Query"})

@app.get("/success")
async def success_state_page(request: Request, total_paid: str | None = None):
    return templates.TemplateResponse(request, "success.html", {"request": request, "total_paid": total_paid or "5,499.00"})

@app.get("/{category}/{product_id}/details")
async def product_details_page(request: Request, category: str, product_id: str):
    from bson import ObjectId
    
    query_conditions = []
    try:
        query_conditions.append({"_id": ObjectId(product_id)})
    except Exception:
        pass
    query_conditions.append({"_id": product_id})
    
    query = {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0]
        
    doc = await db["products"].find_one(query)
    if doc:
        spec = doc.get("specification", "apparel")
        return templates.TemplateResponse(request, "product_details.html", {
            "request": request,
            "product_id": product_id,
            "specification": spec
        })
            
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/home")
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})

@app.get("/orders")
async def orders(request : Request):
    return templates.TemplateResponse(request, "orders.html",{"request":request})

@app.get("/cart")
async def cart_page(request: Request):
    return templates.TemplateResponse(request, "cart.html", {"request": request})

@app.get("/confirm")
async def confirm_page(request: Request):
    user = getattr(request.state, "user", None)
    buyer_details = {}
    if user and user.get("phone") and user.get("role") == "buyer":
        try:
            from backend.helper.database import get_pg_connection
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT shop_name, owner_name, phone, city, state FROM buyer WHERE phone = %s",
                        (user["phone"],)
                    )
                    row = cur.fetchone()
                    if row:
                        buyer_details = {
                            "shop_name": row[0],
                            "owner_name": row[1],
                            "phone": row[2],
                            "city": row[3],
                            "state": row[4]
                        }
        except Exception as e:
            print("Postgres buyer details lookup error:", e)

    return templates.TemplateResponse(request, "confirm.html", {"request": request, "buyer_details": buyer_details})

@app.get("/seller")
def seller(request: Request):
    user = getattr(request.state, "user", None)
    seller_details = {}
    if user and user.get("phone"):
        try:
            from backend.helper.database import get_pg_connection
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT company_name, owner_name, city, state, gst_pan, category FROM seller WHERE phone = %s",
                        (user["phone"],)
                    )
                    row = cur.fetchone()
                    if row:
                        seller_details = {
                            "company_name": row[0],
                            "owner_name": row[1],
                            "city": row[2],
                            "state": row[3],
                            "gst_pan": row[4],
                            "category": row[5]
                        }
        except Exception as e:
            print("Postgres seller details lookup error:", e)
            
    return templates.TemplateResponse(request, 
        "seller.html",
        {"request": request, "seller_details": seller_details}
    )

@app.get("/search")
async def search(
    request: Request, 
    q: str | None = None, 
    category: str | None = None, 
    min_price: float | None = None, 
    max_price: float | None = None,
    sort: str | None = None
):
    results = []
    collections_to_search = [
        "apparel", "fmcg", "mobile_accessories", "steel_work", 
        "homeappliances", "pharma", "books", "beauty", "groceries", "kids", "furniture"
    ]
    
    if category and category.lower() in [c.lower() for c in collections_to_search]:
        collections_to_search = [c for c in collections_to_search if c.lower() == category.lower()]
        
    query_regex = {"$regex": q or "", "$options": "i"}
    filter_query = {"is_hidden": {"$ne": True}}
    
    if q:
        filter_query["$or"] = [
            {"name": query_regex},
            {"product_name": query_regex}
        ]
        
    price_filter = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
        
    if price_filter:
        if q:
            filter_query = {
                "is_hidden": {"$ne": True},
                "$and": [
                    {"$or": [{"name": query_regex}, {"product_name": query_regex}]},
                    {"$or": [{"mrp": price_filter}, {"price": price_filter}]}
                ]
            }
        else:
            filter_query["$or"] = [
                {"mrp": price_filter},
                {"price": price_filter}
            ]
            
    for col_name in collections_to_search:
        col = db[col_name]
        cursor = col.find(filter_query)
        async for doc in cursor:
            name = doc.get("name") or doc.get("product_name") or "Unnamed Product"
            price = doc.get("price") or doc.get("mrp") or 0.0
            qty = doc.get("quantity") or doc.get("qty") or 1
            
            images = doc.get("images")
            image = images[0] if images and isinstance(images, list) else doc.get("image")
            if not image:
                if col_name == "apparel":
                    gender = doc.get("gender", "")
                    image = "menjeans.webp" if gender == "Male" else "womentshirt.webp"
                elif col_name == "fmcg":
                    image = "groceries.webp"
                elif col_name == "mobile_accessories":
                    image = "mobile.webp"
                elif col_name == "steel_work":
                    image = "furniture.webp"
                else:
                    image = "default.webp"
            
            results.append({
                "id": str(doc["_id"]),
                "name": name,
                "price": price,
                "quantity": qty,
                "image": image,
                "category": col_name.replace("_", " ").title(),
                "col_name": col_name,
                "description": doc.get("description", "No description available."),
                "stock": doc.get("stock", 100)
            })
            
    if sort == "price_asc":
        results.sort(key=lambda x: x["price"])
    elif sort == "price_desc":
        results.sort(key=lambda x: x["price"], reverse=True)
        
    return templates.TemplateResponse(request, "search.html", {
        "request": request,
        "Products": results,
        "query": q or "",
        "selected_category": category or "",
        "min_price": min_price if min_price is not None else "",
        "max_price": max_price if max_price is not None else "",
        "sort": sort or ""
    })

def normalize_doc(doc, default_image):
    images = doc.get("images")
    image_val = images[0] if images and isinstance(images, list) else doc.get("image") or default_image
    
    spec = "apparel"
    if "steel_grade" in doc:
        spec = "steel_work"
    elif "compatible_model" in doc:
        spec = "mobile_accessories"
    elif "manufacturing_date" in doc:
        spec = "fmcg"
    elif "expiry_date" in doc:
        spec = "pharmacy"
    elif "warranty" in doc:
        spec = "home_appliances"
        
    if default_image == "lipstick.webp":
        spec = "beauty"
    elif default_image == "copy.webp":
        spec = "books"
    elif default_image == "toys.webp":
        spec = "kids"
    elif default_image == "groceries.webp":
        spec = "groceries"
    elif default_image == "furniture.webp":
        spec = "furniture"
    elif default_image == "pharma.webp":
        spec = "pharmacy"
    elif default_image == "computer.webp":
        spec = "home_appliances"
    elif default_image in ["womentshirt.webp", "menjeans.webp"]:
        spec = "apparel"
        
    return {
        "id": str(doc.get("_id")) if doc.get("_id") else "",
        "col_name": spec,
        "name": doc.get("name") or doc.get("product_name") or "Unnamed Product",
        "price": doc.get("price") or doc.get("mrp") or 0.0,
        "image": image_val,
        "quantity": doc.get("quantity") or doc.get("moq") or doc.get("qty") or 1
    }

@app.get("/womens")
async def womens_wear(request: Request):
    
    apparel = await db["apparel"].find(
        {"is_hidden": {"$ne": True}, "gender": {"$in": ["Female", "Unisex"]}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "womentshirt.webp") for p in apparel]

    return templates.TemplateResponse(request, 
        "womens.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/homeappliances")
async def homeappliances(request: Request):
    homeappliances = await db["homeappliances"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "computer.webp") for p in homeappliances]

    return templates.TemplateResponse(request, 
        "homeappliances.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/beauty")
async def beauty(request: Request):
    beauty = await db["beauty"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "lipstick.webp") for p in beauty]

    return templates.TemplateResponse(request, 
        "beauty.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/books")
async def books(request: Request):
    books = await db["books"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "copy.webp") for p in books]

    return templates.TemplateResponse(request, 
        "books.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/groceries")
async def groceries(request: Request):
    groceries = await db["groceries"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    fmcg = await db["fmcg"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "groceries.webp") for p in groceries + fmcg]

    return templates.TemplateResponse(request, 
        "groceries.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/pharma")
async def pharma(request: Request):
    pharma = await db["pharma"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "pharma.webp") for p in pharma]

    return templates.TemplateResponse(request, 
        "pharma.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/kids")
async def kids(request: Request):
    kids = await db["kids"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "toys.webp") for p in kids]

    return templates.TemplateResponse(request, 
        "kids.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/furniture")
async def furniture(request: Request):
    furniture = await db["furniture"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    steel = await db["steel_work"].find(
        {"is_hidden": {"$ne": True}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "furniture.webp") for p in furniture + steel]

    return templates.TemplateResponse(request, 
        "furniture.html",
        {
            "request": request,
            "Products": products
        }
    )

@app.get("/mens-wear")
async def mens_wear(request: Request):
    # menswear = await db["menswear"].find(
    #     {"is_hidden": {"$ne": True}}, {"_id": 0}
    # ).to_list(length=100)
    
    apparel = await db["apparel"].find(
        {"is_hidden": {"$ne": True}, "gender": {"$in": ["Male", "Unisex"]}}
    ).to_list(length=100)
    
    products = [normalize_doc(p, "menjeans.webp") for p in apparel]

    return templates.TemplateResponse(request, 
        "mens-wear.html",
        {
            "request": request,
            "Products": products
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)