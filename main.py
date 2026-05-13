from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes import getrequests, postrequests
from backend.helper import search
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()


app = FastAPI()

app.include_router(getrequests.router)
app.include_router(postrequests.router)
app.include_router(search.router)
app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)

templates = Jinja2Templates(directory="frontend/templates")

@app.get("/home")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/orders")
async def orders(request : Request):
    return templates.TemplateResponse("orders.html",{"request":request})

@app.get("/credits")
async def credits(request : Request):
    return templates.TemplateResponse("credits.html",{"request" : request})

@app.get("/manufacturer")
async def manufacture(request : Request):
    return templates.TemplateResponse("manufacturer.html",{"request" : request})

@app.get("/womens")
async def womens(request : Request):
    return templates.TemplateResponse("womens.html",{"request" : request})

@app.get("/men")
def men(request : Request):
    return templates.TemplateResponse("men.html",{"request" : request})

@app.get("/search")
async def search(request : Request):
    return templates.TemplateResponse("search.html",{"request":request})

@app.get("/homeappliances")
async def homeappliances(request : Request):
    return templates.TemplateResponse("homeappliances.html",{"request" : request})

@app.get("/beauty")
async def beauty(request : Request):
    return templates.TemplateResponse("beauty.html",{"request" : request})

@app.get("/books")
async def books(request : Request):
    return templates.TemplateResponse("books.html",{"request" : request})

@app.get("/groceries")
async def groceries(request : Request):
    return templates.TemplateResponse("groceries.html",{"request" : request})

@app.get("/pharma")
async def pharma(request : Request):
    return templates.TemplateResponse("pharma.html",{"request" : request})

@app.get("/kids")
async def kids(request : Request):
    return templates.TemplateResponse("kids.html",{"request" : request})

@app.get("/furniture")
async def furniture(request : Request):
    return templates.TemplateResponse("furniture.html",{"request" : request})

@app.get("/")
async def login_page(request : Request):
    return templates.TemplateResponse("login.html",{"request" : request})

#####


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
cluster = os.getenv("MONGO_CLUSTER")

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URI)

db = client["Products"]

@app.get("/mens-wear")
async def mens_wear(request: Request):

    menswear = await db["menswear"].find(
        {}, {"_id": 0}
    ).to_list(length=100)

    return templates.TemplateResponse(
        "mens-wear.html",
        {
            "request": request,
            "Products": menswear
        }
    )