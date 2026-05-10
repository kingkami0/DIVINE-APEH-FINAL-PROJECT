"""
test_api.py — Full test suite for the Cloud E-Commerce REST API.

Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DATABASE import Base, get_db
from main import app


# ── Test DATABASE setup ───────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_ecommerce.db"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)

TestSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Fresh DATABASE for every test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """Client pre-authenticated with a test account."""

    client.post(
        "/auth/register",
        json={
            "email": "test@test.com",
            "password": "secret123"
        }
    )

    resp = client.post(
        "/auth/login",
        data={
            "username": "test@test.com",
            "password": "secret123"
        }
    )

    token = resp.json()["access_token"]

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    return client


# ── Helper ────────────────────────────────────────────────────────────────────

def make_product(client, name="Widget", price=25.0, stock=100):
    return client.post(
        "/products/",
        json={
            "name": name,
            "price": price,
            "stock": stock
        }
    ).json()["id"]


# ═════════════════════════════════════════════════════════════════════════════
# AUTH TESTS
# ═════════════════════════════════════════════════════════════════════════════

def test_register_new_user(client):
    r = client.post(
        "/auth/register",
        json={
            "email": "alice@test.com",
            "password": "pass1234"
        }
    )

    assert r.status_code == 201
    assert r.json()["email"] == "alice@test.com"
    assert "hashed_password" not in r.json()


def test_register_duplicate_email_returns_400(client):
    client.post(
        "/auth/register",
        json={
            "email": "bob@test.com",
            "password": "pass"
        }
    )

    r = client.post(
        "/auth/register",
        json={
            "email": "bob@test.com",
            "password": "other"
        }
    )

    assert r.status_code == 400


def test_login_returns_token(client):
    client.post(
        "/auth/register",
        json={
            "email": "carol@test.com",
            "password": "mypass"
        }
    )

    r = client.post(
        "/auth/login",
        data={
            "username": "carol@test.com",
            "password": "mypass"
        }
    )

    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={
            "email": "dave@test.com",
            "password": "correct"
        }
    )

    r = client.post(
        "/auth/login",
        data={
            "username": "dave@test.com",
            "password": "wrong"
        }
    )

    assert r.status_code == 401


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT TESTS
# ═════════════════════════════════════════════════════════════════════════════

def test_list_products_is_public(client):
    r = client.get("/products/")
    assert r.status_code == 200


def test_create_product_without_auth_returns_401(client):
    r = client.post(
        "/products/",
        json={
            "name": "X",
            "price": 10.0
        }
    )

    assert r.status_code == 401


def test_create_product(auth_client):
    r = auth_client.post(
        "/products/",
        json={
            "name": "Laptop",
            "price": 999.99,
            "stock": 10
        }
    )

    assert r.status_code == 201

    d = r.json()

    assert d["name"] == "Laptop"
    assert d["price"] == 999.99


def test_get_product_by_id(auth_client):
    pid = make_product(auth_client, "Phone", 499.0, 5)

    r = auth_client.get(f"/products/{pid}")

    assert r.status_code == 200
    assert r.json()["name"] == "Phone"


def test_get_nonexistent_product_returns_404(client):
    assert client.get("/products/9999").status_code == 404


def test_update_product_price(auth_client):
    pid = make_product(auth_client)

    r = auth_client.put(
        f"/products/{pid}",
        json={"price": 15.0}
    )

    assert r.status_code == 200
    assert r.json()["price"] == 15.0


def test_delete_product(auth_client):
    pid = make_product(auth_client)

    assert auth_client.delete(f"/products/{pid}").status_code == 204
    assert auth_client.get(f"/products/{pid}").status_code == 404


def test_invalid_price_returns_422(auth_client):
    r = auth_client.post(
        "/products/",
        json={
            "name": "Bad",
            "price": -5,
            "stock": 1
        }
    )

    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════════════
# ORDER TESTS
# ═════════════════════════════════════════════════════════════════════════════

def test_orders_require_auth(client):
    assert client.get("/orders/").status_code == 401


def test_create_order(auth_client):
    pid = make_product(auth_client)

    r = auth_client.post(
        "/orders/",
        json={
            "customer_name": "Alice",
            "customer_email": "alice@test.com",
            "items": [
                {
                    "product_id": pid,
                    "quantity": 3
                }
            ]
        }
    )

    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_order_reduces_stock(auth_client):
    pid = make_product(auth_client, stock=50)

    auth_client.post(
        "/orders/",
        json={
            "customer_name": "Bob",
            "customer_email": "bob@test.com",
            "items": [
                {
                    "product_id": pid,
                    "quantity": 10
                }
            ]
        }
    )

    assert auth_client.get(
        f"/products/{pid}"
    ).json()["stock"] == 40


def test_insufficient_stock_returns_400(auth_client):
    pid = make_product(auth_client, stock=5)

    r = auth_client.post(
        "/orders/",
        json={
            "customer_name": "Charlie",
            "customer_email": "c@test.com",
            "items": [
                {
                    "product_id": pid,
                    "quantity": 999
                }
            ]
        }
    )

    assert r.status_code == 400


def test_order_invalid_product_returns_404(auth_client):
    r = auth_client.post(
        "/orders/",
        json={
            "customer_name": "Dave",
            "customer_email": "d@test.com",
            "items": [
                {
                    "product_id": 9999,
                    "quantity": 1
                }
            ]
        }
    )

    assert r.status_code == 404


def test_update_order_status(auth_client):
    pid = make_product(auth_client)

    oid = auth_client.post(
        "/orders/",
        json={
            "customer_name": "Eve",
            "customer_email": "e@test.com",
            "items": [
                {
                    "product_id": pid,
                    "quantity": 1
                }
            ]
        }
    ).json()["id"]

    r = auth_client.patch(
        f"/orders/{oid}/status",
        json={"status": "shipped"}
    )

    assert r.status_code == 200
    assert r.json()["status"] == "shipped"


def test_delete_order(auth_client):
    pid = make_product(auth_client)

    oid = auth_client.post(
        "/orders/",
        json={
            "customer_name": "Frank",
            "customer_email": "f@test.com",
            "items": [
                {
                    "product_id": pid,
                    "quantity": 1
                }
            ]
        }
    ).json()["id"]

    assert auth_client.delete(
        f"/orders/{oid}"
    ).status_code == 204

    assert auth_client.get(
        f"/orders/{oid}"
    ).status_code == 404