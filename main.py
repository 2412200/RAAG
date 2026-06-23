from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes import getrequests, postrequests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

load_dotenv()


app = FastAPI()

app.include_router(getrequests.router)
app.include_router(postrequests.router)
app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)

templates = Jinja2Templates(directory="frontend/templates")

username = quote_plus(os.getenv("MONGO_USERNAME"))
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster = quote_plus(os.getenv("MONGO_CLUSTER"))

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URI)

db = client["Products"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_please_change")
ALGORITHM = "HS256"

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Paths that don't require authentication
    public_paths = ["/", "/signup", "/POST/login", "/POST/signup", "/logout", "/POST/request-otp"]
    
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
            "/home", "/orders", "/credits", "/search", "/womens", "/mens-wear", 
            "/homeappliances", "/beauty", "/books", "/groceries", "/pharma", "/kids", "/furniture",
            "/POST/order"
        ]
        
        if role == "buyer" and path in seller_paths:
            if request.method == "GET":
                return RedirectResponse(url="/home", status_code=303)
            return JSONResponse(status_code=403, content={"detail": "Access denied. Sellers only."})
            
        if role == "seller" and path in buyer_paths:
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

@app.get("/home")
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})

@app.get("/orders")
async def orders(request : Request):
    return templates.TemplateResponse(request, "orders.html",{"request":request})

@app.get("/credits")
async def credits(request: Request):
    user = getattr(request.state, "user", None)
    shop_name = "Buyer Account"
    
    if user and user.get("phone"):
        try:
            from backend.helper.database import get_pg_connection
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT shop_name FROM buyer WHERE phone = %s", (user["phone"],))
                    row = cur.fetchone()
                    if row:
                        shop_name = row[0]
        except Exception as e:
            print("Postgres credit lookup error:", e)

    # Mock dynamic credit details
    credit_limit = 500000.0
    used_credit = 145000.0
    available_credit = credit_limit - used_credit
    
    ledger = [
        {"date": "2026-06-12", "ref": "INV-2026-089", "desc": "Purchase - Apparel & FMCG", "amount": -85000.0, "status": "Settled"},
        {"date": "2026-06-05", "ref": "PAY-10022", "desc": "Bank Transfer Payment", "amount": 50000.0, "status": "Completed"},
        {"date": "2026-05-28", "ref": "INV-2026-054", "desc": "Purchase - Kids Toys", "amount": -110000.0, "status": "Settled"},
        {"date": "2026-05-20", "ref": "PAY-10009", "desc": "Cheque Settlement", "amount": 100000.0, "status": "Completed"}
    ]
    
    return templates.TemplateResponse(request, "credits.html", {
        "request": request,
        "shop_name": shop_name,
        "credit_limit": credit_limit,
        "used_credit": used_credit,
        "available_credit": available_credit,
        "ledger": ledger
    })

@app.get("/seller")
async def seller(request: Request):
    return templates.TemplateResponse(request, 
        "seller.html",
        {"request": request}
    )

@app.get("/search")
async def search(request: Request, q: str = None):
    results = []
    if q:
        query_regex = {"$regex": q, "$options": "i"}
        collections_to_search = [
            "menswear", "womenswear", "kids", "books", "beauty", 
            "homeappliances", "pharma", "groceries", "furniture",
            "apparel", "fmcg", "mobile_accessories", "steel_work"
        ]
        for col_name in collections_to_search:
            col = db[col_name]
            cursor = col.find({
                "$or": [
                    {"name": query_regex},
                    {"product_name": query_regex}
                ]
            })
            async for doc in cursor:
                name = doc.get("name") or doc.get("product_name") or "Unnamed Product"
                price = doc.get("price") or doc.get("mrp") or 0.0
                qty = doc.get("quantity") or doc.get("qty") or 1
                
                # Check for image or fallback to smart defaults
                image = doc.get("image")
                if not image:
                    if col_name == "apparel":
                        gender = doc.get("gender", "")
                        image = "menjeans.webp" if gender == "Male" else "womentshirt.webp"
                    elif col_name == "fmcg":
                        image = "groceries.webp"
                    elif col_name == "mobile_accessories":
                        image = "bottle.webp"
                    elif col_name == "steel_work":
                        image = "Dining Table.webp"
                    else:
                        image = "default.webp"
                
                results.append({
                    "name": name,
                    "price": price,
                    "quantity": qty,
                    "image": image,
                    "category": col_name.replace("_", " ").title()
                })
    
    return templates.TemplateResponse(request, "search.html", {
        "request": request,
        "Products": results,
        "query": q or ""
    })

@app.get("/womens")
async def womens_wear(request: Request):

    womenswear = await db["womenswear"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "womens.html",
        {
            "request": request,
            "Products": womenswear
        }
    )

@app.get("/homeappliances")
async def homeappliances(request: Request):

    homeappliances = await db["homeappliances"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "homeappliances.html",
        {
            "request": request,
            "Products": homeappliances
        }
    )

@app.get("/beauty")
async def beauty(request: Request):

    beauty = await db["beauty"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "beauty.html",
        {
            "request": request,
            "Products": beauty
        }
    )

@app.get("/books")
async def books(request: Request):

    books = await db["books"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "books.html",
        {
            "request": request,
            "Products": books
        }
    )

@app.get("/groceries")
async def groceries(request: Request):

    groceries = await db["groceries"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "groceries.html",
        {
            "request": request,
            "Products": groceries
        }
    )

@app.get("/pharma")
async def pharma(request: Request):

    pharma = await db["pharma"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "pharma.html",
        {
            "request": request,
            "Products": pharma
        }
    )

@app.get("/kids")
async def kids(request: Request):

    kids = await db["kids"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "kids.html",
        {
            "request": request,
            "Products": kids
        }
    )

@app.get("/furniture")
async def furniture(request: Request):

    furniture = await db["furniture"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "furniture.html",
        {
            "request": request,
            "Products": furniture
        }
    )

@app.get("/mens-wear")
async def mens_wear(request: Request):

    menswear = await db["menswear"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(request, 
        "mens-wear.html",
        {
            "request": request,
            "Products": menswear
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)