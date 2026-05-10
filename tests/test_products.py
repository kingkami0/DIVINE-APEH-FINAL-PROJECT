"""Unit tests for /products — public reads, protected writes."""


def test_list_products_public(client):
    r = client.get("/products/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_product_requires_auth(client):
    r = client.post("/products/", json={"name": "X", "price": 10.0})
    assert r.status_code == 401


def test_create_product(auth_client):
    r = auth_client.post("/products/", json={"name": "Laptop", "price": 999.99, "stock": 10})
    assert r.status_code == 201
    d = r.json()
    assert d["name"] == "Laptop"
    assert d["price"] == 999.99
    assert d["stock"] == 10


def test_get_product_by_id(auth_client):
    pid = auth_client.post("/products/", json={"name": "Phone", "price": 499.0, "stock": 5}).json()["id"]
    r = auth_client.get(f"/products/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Phone"


def test_get_product_not_found(client):
    assert client.get("/products/9999").status_code == 404


def test_update_product(auth_client):
    pid = auth_client.post("/products/", json={"name": "Tablet", "price": 299.0, "stock": 3}).json()["id"]
    r = auth_client.put(f"/products/{pid}", json={"price": 249.0})
    assert r.status_code == 200
    assert r.json()["price"] == 249.0


def test_delete_product(auth_client):
    pid = auth_client.post("/products/", json={"name": "Watch", "price": 199.0, "stock": 7}).json()["id"]
    assert auth_client.delete(f"/products/{pid}").status_code == 204
    assert auth_client.get(f"/products/{pid}").status_code == 404


def test_invalid_price_rejected(auth_client):
    r = auth_client.post("/products/", json={"name": "Bad", "price": -5, "stock": 1})
    assert r.status_code == 422
