"""
Orders router — HTTP layer only.
All business logic lives in services/order_service.py.
All order endpoints require a valid JWT token.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from DATABASE import get_db
from auth import get_current_user
from models import User
import services.order_service as svc

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., example=1)
    quantity:   int = Field(..., gt=0, example=2)

class OrderCreate(BaseModel):
    customer_name:  str                   = Field(..., example="Jane Smith")
    customer_email: str                   = Field(..., example="jane@example.com")
    items:          List[OrderItemCreate]

class StatusUpdate(BaseModel):
    status: str = Field(..., example="shipped")

class OrderItemOut(BaseModel):
    product_id: int
    quantity:   int
    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id:             int
    customer_name:  str
    customer_email: str
    status:         str
    created_at:     datetime
    items:          List[OrderItemOut]
    class Config:
        orm_mode = True

# ── All order endpoints are protected ────────────────────────────────────────

@router.get("/", response_model=list[OrderOut], summary="List all orders 🔒")
def list_orders(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    return svc.get_all(db)


@router.get("/{order_id}", response_model=OrderOut, summary="Get an order 🔒")
def get_order(
    order_id: int,
    db:       Session = Depends(get_db),
    _:        User    = Depends(get_current_user),
):
    return svc.get_or_404(order_id, db)


@router.post("/", response_model=OrderOut, status_code=201, summary="Place an order 🔒")
def create_order(
    body: OrderCreate,
    db:   Session = Depends(get_db),
    _:    User    = Depends(get_current_user),
):
    items = [item.dict() for item in body.items]
    return svc.create(body.customer_name, body.customer_email, items, db)


@router.patch("/{order_id}/status", response_model=OrderOut, summary="Update order status 🔒")
def update_status(
    order_id: int,
    body:     StatusUpdate,
    db:       Session = Depends(get_db),
    _:        User    = Depends(get_current_user),
):
    return svc.update_status(order_id, body.status, db)


@router.delete("/{order_id}", status_code=204, summary="Delete an order 🔒")
def delete_order(
    order_id: int,
    db:       Session = Depends(get_db),
    _:        User    = Depends(get_current_user),
):
    svc.delete(order_id, db)
