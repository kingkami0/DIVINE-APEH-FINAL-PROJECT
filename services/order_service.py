"""
Order business logic — stock validation and atomic deduction live here,
not in the router.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Order, OrderItem, Product


def get_all(db: Session) -> list[Order]:
    return db.query(Order).all()


def get_or_404(order_id: int, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def create(customer_name: str, customer_email: str, items: list[dict], db: Session) -> Order:
    """
    Place an order.
    - Validates each product exists.
    - Checks sufficient stock.
    - Deducts stock atomically (rolls back on any failure).
    """
    order = Order(customer_name=customer_name, customer_email=customer_email)
    db.add(order)
    db.flush()  # get order.id without committing yet

    for item in items:
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=404,
                detail=f"Product with id={item['product_id']} not found"
            )
        if product.stock < item["quantity"]:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product.name}' (available: {product.stock})"
            )
        product.stock -= item["quantity"]
        db.add(OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
        ))

    db.commit()
    db.refresh(order)
    return order


def update_status(order_id: int, new_status: str, db: Session) -> Order:
    order = get_or_404(order_id, db)
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def delete(order_id: int, db: Session) -> None:
    order = get_or_404(order_id, db)
    db.delete(order)
    db.commit()
