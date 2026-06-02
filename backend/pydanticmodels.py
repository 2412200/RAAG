from pydantic import BaseModel ,EmailStr
from pydantic.fields import Field
from typing import Literal,LiteralString, List
from datetime import datetime
from enum import Enum
from datetime import date

class Order_items(BaseModel):
    itemname : List[str]
    quantity : List[int] = Field(gt=1)

class SignupRequest(BaseModel):
    company: str
    phone: str
    address: str
    password: str
    role: str

class LoginRequest(BaseModel):
    phone: str
    password: str
    role: str

#class product_specification(BaseModel):



#used in apparel
class SizeEnum(str,Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"


class apparel(BaseModel):
    product_name : str
    size : SizeEnum
    fabric : str
    category : Literal["Mens Shirt", "Mens TShirt", "Mens Lower", "Mens Jeans", "Mens Shorts", 
                       "Pyjama", "Mens Inner Wear", "Womens Shirt", "Womens Jeans", "Womens TShirt",
                       "Womens Lower", "Womens Pyjama"]
    gsm : int = Field(gt=1)
    mrp : float = Field(gt=1)
    gender : Literal["Male", "Female"]

class fmcg(BaseModel):
    product_name : str
    brand : str
    category : Literal['Food', "Beverage","Personal Care", "Household"]
    quantity : int = Field(gt=1)
    mrp : float = Field(gt=1)
    manufacturing_date : date
    expiry_date : date

class mobile_accessories(BaseModel):
    product_name : str
    brand : str
    compatible_model : str
    accessory_type : Literal["Charger", "Case", "Cable", "Earphone", "Power Bank", "Screen Protector",
                             "Holder/Stand"]
    color : str
    warranty : int = Field(gt = 1)
    mrp : float = Field(gt = 1)

class steel_work(BaseModel):
    product_name : str
    steel_grade : str
    thickness : float
    weight : float
    finish_type : Literal["Mill Finish", "Polished", "Brushed", "Matte", "Galvanized", "Powder Coated"]
    mrp : float

            