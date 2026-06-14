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
    public_paths = ["/", "/signup", "/POST/login", "/POST/signup"]
    
    if request.url.path in public_paths or request.url.path.startswith("/static"):
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
async def credits(request : Request):
    return templates.TemplateResponse(request, "credits.html",{"request" : request})

@app.get("/manufacturer")
async def manufacturer(request: Request):
    return templates.TemplateResponse(request, 
        "manufacturer.html",
        {"request": request}
    )

@app.get("/search")
async def search(request : Request):
    return templates.TemplateResponse(request, "search.html",{"request":request})

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