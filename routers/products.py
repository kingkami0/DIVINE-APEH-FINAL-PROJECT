"""
Products router — HTTP layer only.
All business logic lives in services/product_service.py.
Write operations (POST / PUT / DELETE) require a valid JWT token.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from DATABASE import get_db
from auth import get_current_user
from models import User
import services.product_service as svc

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name:        str   = Field(..., example="Laptop Pro 15")
    description: Optional[str] = Field(None, example="High-performance laptop")
    price:       float = Field(..., gt=0, example=999.99)
    stock:       int   = Field(0, ge=0, example=50)

class ProductUpdate(BaseModel):
    name:        Optional[str]   = None
    description: Optional[str]   = None
    price:       Optional[float] = Field(None, gt=0)
    stock:       Optional[int]   = Field(None, ge=0)

class ProductOut(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    price:       float
    stock:       int

    class Config:
        orm_mode = True

# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/", response_model=list[ProductOut], summary="List all products")
def list_products(db: Session = Depends(get_db)):
    return svc.get_all(db)


@router.get("/{product_id}", response_model=ProductOut, summary="Get a product")
def get_product(product_id: int, db: Session = Depends(get_db)):
    return svc.get_or_404(product_id, db)


# ── Protected endpoints (JWT required) ────────────────────────────────────────

@router.post("/", response_model=ProductOut, status_code=201, summary="Create a product 🔒")
def create_product(
    body: ProductCreate,
    db:   Session = Depends(get_db),
    _:    User    = Depends(get_current_user),   # enforces auth
):
    return svc.create(body.dict(), db)


@router.put("/{product_id}", response_model=ProductOut, summary="Update a product 🔒")
def update_product(
    product_id: int,
    body:       ProductUpdate,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    return svc.update(product_id, body.dict(exclude_unset=True), db)


@router.delete("/{product_id}", status_code=204, summary="Delete a product 🔒")
def delete_product(
    product_id: int,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    svc.delete(product_id, db)
