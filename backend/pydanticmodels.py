from pydantic import BaseModel , model_validator
from pydantic.fields import Field
from typing import Literal, List, Optional
from enum import Enum
from datetime import date
from datetime import datetime

class order_item(BaseModel):
    product_name: str
    quantity: int
    price: float

class orders(BaseModel):
    customer_name: str
    customer_number: int

    products: List[order_item]

    total_amount: float
    order_status: str = "Pending"

    created_at: datetime = Field(default_factory=datetime.now)

class SignupRequest(BaseModel):
    business_name: str
    owner_name: str
    phone: str
    city: str
    state: str
    password: str
    role: str
    gst_pan: Optional[str] = None
    category: Optional[str] = None
    otp: Optional[str] = None

    @model_validator(mode="after")
    def validate_seller_fields(self):
        if not self.category or not self.category.strip():
            raise ValueError("Category is required")
        valid_categories = ["home appliances", "apparels", "pharmacy", "steel work", "fmcg"]
        if self.category not in valid_categories:
            raise ValueError(f"Category must be one of {valid_categories}")

        if self.role == "seller":
            if not self.gst_pan or not self.gst_pan.strip():
                raise ValueError("GST/PAN number is required for sellers")
        return self

class LoginRequest(BaseModel):
    phone: str
    password: str
    role: str

class SizeEnum(str,Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    S24 = "24"
    S26 = "26"
    S28 = "28"
    S30 = "30"
    S32 = "32"
    S34 = "34"
    S36 = "36"


class apparel(BaseModel):
    product_name : str
    size : List[SizeEnum]
    fabric : str
    category : Literal["Mens Shirt", "Mens TShirt", "Mens Lower", "Mens Jeans", "Mens Shorts", 
                       "Pyjama", "Mens Inner Wear", "Womens Shirt", "Womens Jeans", "Womens TShirt",
                       "Womens Lower", "Womens Pyjama", "Mens Trouser", "Womens Trouser"]
    gsm : int = Field(gt=1)
    mrp : float = Field(gt=1)
    gender : Literal["Male", "Female", "Unisex"]
    moq: int = Field(default=1, gt=0)
    seller_phone: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = ""
    images: List[str] = []

class fmcg(BaseModel):
    product_name : str
    brand : str
    category : Literal['Food', "Beverage","Personal Care", "Household"]
    quantity : int = Field(gt=1)
    mrp : float = Field(gt=1)
    manufacturing_date : date
    expiry_date : date 
    seller_phone: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = ""
    images: List[str] = []


    @model_validator(mode="after")
    def validate_dates(self):
        if self.expiry_date <= self.manufacturing_date:
            raise ValueError(
                "expiry_date must be later than manufacturing_date"
            )
        return self

class mobile_accessories(BaseModel):
    product_name : str
    brand : str
    compatible_model : str
    accessory_type : Literal["Charger", "Case", "Cable", "Earphone", "Power Bank", "Screen Protector",
                             "Holder/Stand"]
    color : str
    warranty : int = Field(gt = 1)
    mrp : float = Field(gt = 1)
    seller_phone: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = ""
    images: List[str] = []


class steel_work(BaseModel):
    product_name : str
    steel_grade : str
    thickness : float
    weight : float
    finish_type : Literal["Mill Finish", "Polished", "Brushed", "Matte", "Galvanized", "Powder Coated"]
    mrp : float
    seller_phone: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = ""
    images: List[str] = []


class otp_request(BaseModel):
    phone : str
    role: Literal["buyer", "seller"]

class ToggleVisibilityRequest(BaseModel):
    product_id: str
    specification: str
    is_hidden: bool

class DeleteProductRequest(BaseModel):
    product_id: str
    specification: str

class home_appliances(BaseModel):
    product_name : str
    brand : str
    mrp : float = Field(gt = 1)
    warranty : int = Field(gt = 1)
    seller_phone: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = ""
    images: List[str] = []

class pharmacy(BaseModel):
    product_name : str
    brand : str
    category : Literal["Food", "Beverage", "Personal Care", "Household", "Medicine", "First Aid"]
    mrp : float = Field(gt = 1)
    expiry_date : date
    seller_phone: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = ""
    images: List[str] = []

class ForgotPasswordOTPRequest(BaseModel):
    phone: str
    role: Literal["buyer", "seller"]

class ResetPasswordRequest(BaseModel):
    phone: str
    role: Literal["buyer", "seller"]
    otp: str
    password: str