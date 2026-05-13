from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
load_dotenv()

username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
cluster  = os.getenv("MONGO_CLUSTER")

client = MongoClient(f"mongodb+srv://{username}:{password}@{cluster}/products")
db = client["Products"]
db["menswear"].insert_many([
    { "name": "T Shirt",      "image": "mentshirt.webp",     "quantity": 10, "price": 50000  },
    { "name": "Shirt",        "image": "menshirt.webp",      "quantity": 10, "price": 500000 },
    { "name": "Kurta",        "image": "menkurta.webp",      "quantity": 10, "price": 50000  },
    { "name": "Jeans",        "image": "menjeans.webp",      "quantity": 10, "price": 100000 },
    { "name": "Formal Jeans", "image": "mensformaljeans.webp","quantity": 10, "price": 70000  },
    { "name": "Jacket",       "image": "mensjacket.webp",    "quantity": 10, "price": 80000  },
    { "name": "Sweater",      "image": "menssweater.webp",   "quantity": 10, "price": 80000  },
    { "name": "Trouser",      "image": "menstrouser.webp",   "quantity": 10, "price": 80000  },
])

print("Products inserted!")