from pydantic import BaseModel,EmailStr
from pydantic.fields import Field


class ModelWarehouse(BaseModel):
    name : str = Field(...)
    address : str = Field(...)
    product : str = Field(...)
    quantity : int = Field(...)
    priceperpiece : float = Field(...)
    phone_number : str = Field(...)
    email : EmailStr = Field(...)
    owner : str = Field(...)

