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

