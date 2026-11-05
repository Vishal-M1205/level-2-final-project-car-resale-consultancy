from app.core.security import create_access_token
from tests.conftest import create_db_user


def test_get_users_admin_success(client, admin_headers):
    create_db_user(email="user_a@example.com", phone="9876543201", role="CUSTOMER")
    create_db_user(email="user_b@example.com", phone="9876543202", role="CONSULTANT")

    response = client.get("/api/users/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total_users" in data
    assert data["total_users"] >= 2


def test_get_users_customer_forbidden(client, customer_headers):
    response = client.get("/api/users/", headers=customer_headers)
    assert response.status_code == 403


def test_get_user_by_id_admin_success(client, admin_headers):
    user = create_db_user(email="get_id@example.com", phone="9876543203")
    response = client.get(f"/api/users/{user['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "get_id@example.com"


def test_get_user_by_id_not_found(client, admin_headers):
    response = client.get("/api/users/99999", headers=admin_headers)
    assert response.status_code == 404


def test_patch_user_own_profile_success(client, customer_headers, customer_user):
    payload = {"name": "Updated Customer Name", "district": "Madurai"}
    response = client.patch(
        f"/api/users/{customer_user['id']}", json=payload, headers=customer_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Customer Name"
    assert data["district"] == "Madurai"


def test_patch_user_duplicate_phone(client, customer_headers, customer_user):
    create_db_user(email="phone_owner@example.com", phone="9876543204")
    response = client.patch(
        f"/api/users/{customer_user['id']}",
        json={"phone": "9876543204"},
        headers=customer_headers,
    )
    assert response.status_code == 409


def test_patch_other_user_forbidden(client, customer_headers, buyer_user):
    response = client.patch(
        f"/api/users/{buyer_user['id']}",
        json={"name": "Hacked Name"},
        headers=customer_headers,
    )
    assert response.status_code == 403


def test_soft_delete_user_admin_success(client, admin_headers):
    user = create_db_user(email="to_delete@example.com", phone="9876543205")
    response = client.delete(f"/api/users/{user['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert "successfully deactivated" in response.json()["message"].lower()

    # Second deactivation attempt returns 400
    repeat_res = client.delete(f"/api/users/{user['id']}", headers=admin_headers)
    assert repeat_res.status_code == 400


def test_get_my_profile_success(client, customer_headers, customer_user):
    response = client.get("/api/users/me", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == customer_user["id"]
    assert data["email"] == customer_user["email"]


def test_get_my_profile_unauthenticated(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_patch_my_profile_success(client, customer_headers, customer_user):
    payload = {"name": "Self Updated Name", "district": "Salem"}
    response = client.patch("/api/users/me", json=payload, headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Self Updated Name"
    assert data["district"] == "Salem"


def test_get_users_query_params_filters(client, admin_headers):
    create_db_user(
        name="Alpha User",
        email="alpha_filter@example.com",
        phone="9876543206",
        role="CUSTOMER",
        district="Madurai",
    )
    create_db_user(
        name="Beta Consultant",
        email="beta_filter@example.com",
        phone="9876543207",
        role="CONSULTANT",
        district="Chennai",
    )

    # Filter by search keyword
    res_search = client.get("/api/users/?search=Alpha", headers=admin_headers)
    assert res_search.status_code == 200
    assert any(u["email"] == "alpha_filter@example.com" for u in res_search.json()["users"])
    assert not any(u["email"] == "beta_filter@example.com" for u in res_search.json()["users"])

    # Filter by role
    res_role = client.get("/api/users/?role=CONSULTANT", headers=admin_headers)
    assert res_role.status_code == 200
    assert all(u["role"] == "CONSULTANT" for u in res_role.json()["users"])

    # Filter by district
    res_district = client.get("/api/users/?district=Madurai", headers=admin_headers)
    assert res_district.status_code == 200
    assert any(u["district"] == "Madurai" for u in res_district.json()["users"])

    # Filter with sort_by and order
    res_sorted = client.get("/api/users/?sort_by=name&order=asc", headers=admin_headers)
    assert res_sorted.status_code == 200
    names = [u["name"] for u in res_sorted.json()["users"]]
    assert names == sorted(names, key=lambda s: s.lower())


def test_deactivated_user_token_rejected(client):
    create_db_user(
        email="deactivated_bearer@example.com",
        phone="9876543299",
        is_active=False,
    )
    token = create_access_token({"sub": "deactivated_bearer@example.com", "role": "CUSTOMER"})
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()
