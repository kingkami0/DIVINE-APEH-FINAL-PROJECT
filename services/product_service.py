"""
Product business logic — separated from the HTTP layer (router).
Routers call these functions; they never touch the DB directly.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Product


def get_all(db: Session) -> list[Product]:
    return db.query(Product).all()


def get_or_404(product_id: int, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def create(data: dict, db: Session) -> Product:
    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update(product_id: int, data: dict, db: Session) -> Product:
    product = get_or_404(product_id, db)
    for field, value in data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete(product_id: int, db: Session) -> None:
    product = get_or_404(product_id, db)
    db.delete(product)
    db.commit()
