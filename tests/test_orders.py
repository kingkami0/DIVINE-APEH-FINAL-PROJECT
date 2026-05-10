"""Unit tests for /orders — all endpoints require auth."""


def _make_product(client, stock=100):
    return client.post("/products/", json={"name": "Widget", "price": 25.0, "stock": stock}).json()["id"]


def test_create_order(auth_client):
    pid = _make_product(auth_client)
    r = auth_client.post("/orders/", json={
        "customer_name": "Alice",
        "customer_email": "alice@test.com",
        "items": [{"product_id": pid, "quantity": 3}]
    })
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_order_deducts_stock(auth_client):
    pid = _make_product(auth_client, stock=50)
    auth_client.post("/orders/", json={
        "customer_name": "Bob", "customer_email": "bob@test.com",
        "items": [{"product_id": pid, "quantity": 10}]
    })
    assert auth_client.get(f"/products/{pid}").json()["stock"] == 40


def test_insufficient_stock_returns_400(auth_client):
    pid = _make_product(auth_client, stock=5)
    r = auth_client.post("/orders/", json={
        "customer_name": "Charlie", "customer_email": "c@test.com",
        "items": [{"product_id": pid, "quantity": 999}]
    })
    assert r.status_code == 400
    assert "Insufficient" in r.json()["detail"]


def test_order_product_not_found(auth_client):
    r = auth_client.post("/orders/", json={
        "customer_name": "Dave", "customer_email": "d@test.com",
        "items": [{"product_id": 9999, "quantity": 1}]
    })
    assert r.status_code == 404


def test_update_order_status(auth_client):
    pid = _make_product(auth_client)
    oid = auth_client.post("/orders/", json={
        "customer_name": "Eve", "customer_email": "e@test.com",
        "items": [{"product_id": pid, "quantity": 1}]
    }).json()["id"]
    r = auth_client.patch(f"/orders/{oid}/status", json={"status": "shipped"})
    assert r.status_code == 200
    assert r.json()["status"] == "shipped"


def test_delete_order(auth_client):
    pid = _make_product(auth_client)
    oid = auth_client.post("/orders/", json={
        "customer_name": "Frank", "customer_email": "f@test.com",
        "items": [{"product_id": pid, "quantity": 1}]
    }).json()["id"]
    assert auth_client.delete(f"/orders/{oid}").status_code == 204
    assert auth_client.get(f"/orders/{oid}").status_code == 404


def test_orders_require_auth(client):
    assert client.get("/orders/").status_code == 401
