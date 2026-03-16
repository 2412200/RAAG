from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes import getrequests, postrequests
from backend.helper import search

app = FastAPI()

app.include_router(getrequests.router)
app.include_router(postrequests.router)
app.include_router(search.router)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend/templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/orders")
def orders(request : Request):
    return templates.TemplateResponse("orders.html",{"request":request})

@app.get("/credits")
def credits(request : Request):
    return templates.TemplateResponse("credits.html",{"request" : request})

@app.get("/womens")
def womens(request : Request):
    return templates.TemplateResponse("womens.html",{"request" : request})

@app.get("/men")
def men(request : Request):
    return templates.TemplateResponse("men.html",{"request" : request})

@app.get("/search")
def search(request : Request):
    return templates.TemplateResponse("search.html",{"request":request})

@app.get("/homeappliances")
def homeappliances(request : Request):
    return templates.TemplateResponse("homeappliances.html",{"request" : request})

@app.get("/beauty")
def beauty(request : Request):
    return templates.TemplateResponse("beauty.html",{"request" : request})

@app.get("/books")
def books(request : Request):
    return templates.TemplateResponse("books.html",{"request" : request})

@app.get("/groceries")
def groceries(request : Request):
    return templates.TemplateResponse("groceries.html",{"request" : request})

@app.get("/pharma")
def pharma(request : Request):
    return templates.TemplateResponse("pharma.html",{"request" : request})

@app.get("/kids")
def kids(request : Request):
    return templates.TemplateResponse("kids.html",{"request" : request})

@app.get("/furniture")
def furniture(request : Request):
    return templates.TemplateResponse("furniture.html",{"request" : request})