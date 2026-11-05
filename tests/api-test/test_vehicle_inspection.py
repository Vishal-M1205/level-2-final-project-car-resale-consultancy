from tests.conftest import (
    create_db_inspection,
    create_db_vehicle,
)


def test_get_all_inspections_consultant_success(client, consultant_headers, customer_user):
    v = create_db_vehicle(seller_id=customer_user["id"])
    create_db_inspection(vehicle_id=v["id"], status="PENDING")

    response = client.get("/api/vehicle-inspections/", headers=consultant_headers)
    assert response.status_code == 200
    assert response.json()["total_inspections"] >= 1


def test_get_all_inspections_customer_forbidden(client, customer_headers):
    response = client.get("/api/vehicle-inspections/", headers=customer_headers)
    assert response.status_code == 403


def test_get_all_inspections_filters(client, consultant_headers, customer_user, consultant_user):
    v1 = create_db_vehicle(seller_id=customer_user["id"], registration_number="TN01AA0001")
    v2 = create_db_vehicle(seller_id=customer_user["id"], registration_number="TN01AA0002")
    insp1 = create_db_inspection(vehicle_id=v1["id"], consultant_id=None, status="PENDING")
    create_db_inspection(vehicle_id=v2["id"], consultant_id=consultant_user["id"], status="PENDING")

    # Filter by vehicle_id
    res = client.get(f"/api/vehicle-inspections/?vehicle_id={v1['id']}", headers=consultant_headers)
    assert res.status_code == 200
    assert res.json()["inspections"][0]["id"] == insp1["id"]

    # Filter unclaimed
    res_unclaimed = client.get("/api/vehicle-inspections/?is_claimed=false", headers=consultant_headers)
    assert res_unclaimed.status_code == 200
    unclaimed_ids = [i["id"] for i in res_unclaimed.json()["inspections"]]
    assert insp1["id"] in unclaimed_ids


def test_get_my_inspections_customer_success(
    client, customer_user, buyer_user, customer_headers
):
    v1 = create_db_vehicle(seller_id=customer_user["id"], registration_number="TN01AA0005")
    insp1 = create_db_inspection(vehicle_id=v1["id"])
    v2 = create_db_vehicle(seller_id=buyer_user["id"], registration_number="TN01AA0006")
    create_db_inspection(vehicle_id=v2["id"])

    response = client.get("/api/vehicle-inspections/my-inspections", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_inspections"] == 1
    assert data["inspections"][0]["id"] == insp1["id"]


def test_claim_inspection_consultant_success(
    client, consultant_headers, consultant_user, customer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"])
    insp = create_db_inspection(vehicle_id=v["id"], consultant_id=None, status="PENDING")

    response = client.post(
        f"/api/vehicle-inspections/{insp['id']}/claim",
        headers=consultant_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["consultant_id"] == consultant_user["id"]
    assert data["vehicle_id"] == v["id"]


def test_claim_inspection_already_claimed_conflict(
    client, consultant_headers, consultant_user, customer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"])
    insp = create_db_inspection(vehicle_id=v["id"], consultant_id=consultant_user["id"], status="PENDING")

    response = client.post(
        f"/api/vehicle-inspections/{insp['id']}/claim",
        headers=consultant_headers,
    )
    assert response.status_code == 409


def test_unclaim_inspection_consultant_success(
    client, consultant_headers, consultant_user, customer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"])
    insp = create_db_inspection(vehicle_id=v["id"], consultant_id=consultant_user["id"], status="PENDING")

    response = client.post(
        f"/api/vehicle-inspections/{insp['id']}/unclaim",
        headers=consultant_headers,
    )
    assert response.status_code == 200
    assert "pending pool" in response.json()["message"].lower()


def test_submit_inspection_report_success(
    client, consultant_headers, consultant_user, customer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"])
    insp = create_db_inspection(vehicle_id=v["id"], consultant_id=consultant_user["id"], status="PENDING")

    report_payload = {
        "condition": "good",
        "engine_condition": "excellent",
        "exterior_condition": "good",
        "interior_condition": "good",
        "accident_history": False,
        "estimated_market_value": 560000.0,
        "inspection_notes": "Car runs smoothly.",
    }
    response = client.put(
        f"/api/vehicle-inspections/{insp['id']}",
        json=report_payload,
        headers=consultant_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    assert float(response.json()["estimated_market_value"]) == 560000.0


def test_cancel_inspection_admin_success(client, admin_headers, customer_user):
    v = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    insp = create_db_inspection(vehicle_id=v["id"], status="PENDING")

    response = client.patch(
        f"/api/vehicle-inspections/{insp['id']}/cancel",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inspection_status"] == "CANCELLED"
    assert data["vehicle_status"] == "rejected"

