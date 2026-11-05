from app.core.security import create_access_token, create_refresh_token
from tests.conftest import create_db_user


def test_register_user_success(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "Password@123",
        "phone": "9876543210",
        "age": 28,
        "gender": "FEMALE",
        "address_line_1": "123 Main St",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "pincode": "641001",
    }
    response = client.post("/api/auth/register/user", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["role"] == "CUSTOMER"


def test_register_duplicate_email(client):
    create_db_user(email="dup@example.com", phone="9876543211")
    payload = {
        "name": "Duplicate User",
        "email": "dup@example.com",
        "password": "Password@123",
        "phone": "9876543212",
        "age": 30,
        "gender": "MALE",
        "address_line_1": "Street 1",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600001",
    }
    response = client.post("/api/auth/register/user", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_register_invalid_password(client):
    payload = {
        "name": "Weak Pwd",
        "email": "weak@example.com",
        "password": "simple",  # Fails requirements
        "phone": "9876543213",
        "age": 25,
        "gender": "MALE",
        "address_line_1": "Street",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600001",
    }
    response = client.post("/api/auth/register/user", json=payload)
    assert response.status_code == 422


def test_login_success(client):
    create_db_user(
        email="login_user@example.com", password="Password@123", phone="9876543223"
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "login_user@example.com", "password": "Password@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["type"] == "bearer"


def test_login_wrong_password(client):
    create_db_user(
        email="login_fail@example.com", password="Password@123", phone="9876543224"
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "login_fail@example.com", "password": "WrongPassword@999"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_deactivated_user(client):
    create_db_user(
        email="inactive@example.com",
        password="Password@123",
        phone="9876543225",
        is_active=False,
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "inactive@example.com", "password": "Password@123"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()


def test_refresh_token_success(client):
    create_db_user(email="refresh@example.com", phone="9876543226")
    refresh_token = create_refresh_token({"sub": "refresh@example.com"})
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token


def test_refresh_token_with_access_token_rejected(client):
    create_db_user(email="bad_refresh@example.com", phone="9876543227")
    access_token = create_access_token(
        {"sub": "bad_refresh@example.com", "role": "CUSTOMER"}
    )
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": access_token}
    )
    assert response.status_code == 401

