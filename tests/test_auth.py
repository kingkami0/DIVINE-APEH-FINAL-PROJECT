"""Unit tests for auth endpoints."""


def test_register_success(client):
    r = client.post("/auth/register", json={"email": "alice@test.com", "password": "pass1234"})
    assert r.status_code == 201
    assert r.json()["email"] == "alice@test.com"
    assert "hashed_password" not in r.json()


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "bob@test.com", "password": "pass1234"})
    r = client.post("/auth/register", json={"email": "bob@test.com", "password": "other"})
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"]


def test_login_success(client):
    client.post("/auth/register", json={"email": "carol@test.com", "password": "mypassword"})
    r = client.post("/auth/login", data={"username": "carol@test.com", "password": "mypassword"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "dave@test.com", "password": "correct"})
    r = client.post("/auth/login", data={"username": "dave@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_endpoint_without_token(client):
    """POST /products must reject unauthenticated requests."""
    r = client.post("/products/", json={"name": "Laptop", "price": 999.0, "stock": 5})
    assert r.status_code == 401


def test_protected_endpoint_with_token(auth_client):
    """POST /products must succeed with a valid token."""
    r = auth_client.post("/products/", json={"name": "Laptop", "price": 999.0, "stock": 5})
    assert r.status_code == 201
