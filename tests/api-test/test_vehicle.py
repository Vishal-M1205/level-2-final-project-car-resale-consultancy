from tests.conftest import (
    create_db_inspection,
    create_db_vehicle,
)


def test_submit_vehicle_success(client, customer_headers):
    payload = {
        "brand": "Maruti",
        "model": "Swift",
        "variant": "VXI",
        "registration_number": "TN-01-AB-1234",
        "manufacturing_year": 2021,
        "fuel_type": "PETROL",
        "transmission": "MANUAL",
        "kilometers_driven": 25000,
        "ownership_count": 1,
        "expected_price": 550000.0,
        "description": "Pristine condition first-hand car",
        "seating_capacity": 5,
    }
    response = client.post("/api/vehicles/", json=payload, headers=customer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["brand"] == "Maruti"
    assert data["registration_number"] == "TN01AB1234"
    assert data["status"] == "submitted"


def test_submit_vehicle_duplicate_registration_number(client, customer_headers):
    payload = {
        "brand": "Maruti",
        "model": "Swift",
        "registration_number": "TN01AB1234",
        "manufacturing_year": 2021,
        "fuel_type": "PETROL",
        "transmission": "MANUAL",
        "kilometers_driven": 25000,
        "ownership_count": 1,
        "expected_price": 550000.0,
        "seating_capacity": 5,
    }
    res1 = client.post("/api/vehicles/", json=payload, headers=customer_headers)
    assert res1.status_code == 201

    res2 = client.post("/api/vehicles/", json=payload, headers=customer_headers)
    assert res2.status_code == 409
    assert "already found" in res2.json()["detail"].lower()


def test_get_vehicles_customer_scoped_to_own(
    client, customer_user, buyer_user, customer_headers
):
    v1 = create_db_vehicle(seller_id=customer_user["id"], registration_number="TN01AA1111")
    create_db_vehicle(seller_id=buyer_user["id"], registration_number="TN01BB2222")

    response = client.get("/api/vehicles/", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_vehicles"] == 1
    assert data["vehicles"][0]["id"] == v1["id"]


def test_get_vehicles_admin_sees_all(client, customer_user, buyer_user, admin_headers):
    create_db_vehicle(seller_id=customer_user["id"], registration_number="TN01AA1111")
    create_db_vehicle(seller_id=buyer_user["id"], registration_number="TN01BB2222")

    response = client.get("/api/vehicles/", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["total_vehicles"] >= 2


def test_get_vehicle_by_id_success(client, customer_user, customer_headers):
    v = create_db_vehicle(seller_id=customer_user["id"])
    response = client.get(f"/api/vehicles/{v['id']}", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["id"] == v["id"]


def test_update_submitted_vehicle_success(client, customer_user, customer_headers):
    v = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    response = client.patch(
        f"/api/vehicles/{v['id']}",
        json={"expected_price": 620000.0, "kilometers_driven": 28000},
        headers=customer_headers,
    )
    assert response.status_code == 200
    assert float(response.json()["expected_price"]) == 620000.0


def test_update_approved_vehicle_rejected(client, customer_user, customer_headers):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    response = client.patch(
        f"/api/vehicles/{v['id']}",
        json={"expected_price": 700000.0},
        headers=customer_headers,
    )
    assert response.status_code == 400
    assert "submitted" in response.json()["detail"].lower()


def test_vehicle_decision_approve_creates_listing(client, customer_user, admin_headers):
    import psycopg
    from tests.conftest import config

    v = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    create_db_inspection(
        vehicle_id=v["id"],
        status="COMPLETED",
        estimated_market_value=590000.0,
    )

    # Seed required documents (RC, INSURANCE, PUC)
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            for doc_type in ["RC", "INSURANCE", "PUC"]:
                cur.execute(
                    "INSERT INTO vehicle_documents (vehicle_id, document_type, original_filename, document_url) VALUES (%s, %s, %s, %s)",
                    (v["id"], doc_type, f"{doc_type.lower()}.pdf", f"uploads/{doc_type.lower()}.pdf"),
                )

    response = client.patch(
        f"/api/vehicles/{v['id']}/decision",
        json={"action": "APPROVED"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["listing_id"] is not None

