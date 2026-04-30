from pydantic import BaseModel ,EmailStr
from pydantic.fields import Field
from typing import Literal,LiteralString, List
from datetime import datetime

class ModelWarehouse(BaseModel):
    name : str = Field(...)
    address : str = Field(...)
    product : str = Field(...)
    quantity : int = Field(...)
    priceperpiece : float = Field(...)
    phone_number : str = Field(...)
    email : EmailStr = Field(...)
    owner : str = Field(...)

class Orders(BaseModel):
    retailer_id : int
    warehouseid : int

class Order_items(BaseModel):
    itemname : List[str]
    quantity : List[int] = Field(gt=1)

class apparels(BaseModel):
    productname : str
    size : str
    fabric_name : str
    category : str
    GSM : int
    Price : float
    Gender : str