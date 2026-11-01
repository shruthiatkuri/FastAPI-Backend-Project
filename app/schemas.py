from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

class OrderStatus(str, Enum):
    pending="pending"
    delivered = "delivered"
    paid = "paid"
    shipped = "shipped"
    cancelled = "cancelled"

class OrderCreate(BaseModel):
    user_id: int | None=None
    product_id: int
    quantity: int= Field(gt=0)

class OrderUpdate(BaseModel):
    quantity: int | None= Field(default= None, gt=0)
    status: OrderStatus | None=None

class OrderOut(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    status: str
    created_at: datetime

