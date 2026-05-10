"""
schemas.py — All Pydantic request/response models for the E-Commerce API.
Keeping schemas in one file separates validation from business logic.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="securepassword")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True


# ── Product Schemas ───────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., example="Laptop Pro 15")
    description: Optional[str] = Field(
        None,
        example="High-performance laptop"
    )
    price: float = Field(..., gt=0, example=999.99)
    stock: int = Field(0, ge=0, example=50)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int

    class Config:
        orm_mode = True


# ── Order Schemas ─────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0, example=1)
    quantity: int = Field(..., gt=0, example=2)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., example="Jane Smith")
    customer_email: str = Field(..., example="jane@example.com")
    items: List[OrderItemCreate]


class StatusUpdate(BaseModel):
    status: str = Field(..., example="shipped")


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int

    class Config:
        orm_mode = True


class OrderOut(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    status: str
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        orm_mode = True