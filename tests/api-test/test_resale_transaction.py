import psycopg
from tests.conftest import (
    config,
    create_db_listing,
    create_db_transaction,
    create_db_user,
    create_db_vehicle,
)


def test_create_transaction_admin_success(
    client, admin_headers, customer_user, buyer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], listed_price=600000.0, status="ACTIVE")

    payload = {
        "listing_id": listing["id"],
        "buyer_id": buyer_user["id"],
        "final_price": 590000.0,
        "delivery_notes": "Delivered with original RC and keys.",
    }
    response = client.post("/api/resale-transactions/", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["listing_id"] == listing["id"]
    assert data["buyer_id"] == buyer_user["id"]
    assert data["seller_id"] == customer_user["id"]
    assert float(data["final_price"]) == 590000.0
    assert data["status"] == "CONFIRMED"

    # Verify listing is SOLD and vehicle is sold
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM vehicle_listings WHERE id = %s;", (listing["id"],))
            assert cur.fetchone()[0] == "SOLD"
            cur.execute("SELECT status FROM vehicles WHERE id = %s;", (v["id"],))
            assert cur.fetchone()[0] == "sold"


def test_create_transaction_customer_forbidden(
    client, customer_headers, customer_user, buyer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], status="ACTIVE")

    payload = {
        "listing_id": listing["id"],
        "buyer_id": buyer_user["id"],
        "final_price": 590000.0,
    }
    response = client.post("/api/resale-transactions/", json=payload, headers=customer_headers)
    assert response.status_code == 403


def test_create_transaction_listing_not_active(
    client, admin_headers, customer_user, buyer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], status="INACTIVE")

    payload = {
        "listing_id": listing["id"],
        "buyer_id": buyer_user["id"],
        "final_price": 500000.0,
    }
    response = client.post("/api/resale-transactions/", json=payload, headers=admin_headers)
    assert response.status_code == 400
    assert "only active listings can be sold" in response.json()["detail"].lower()


def test_create_transaction_buyer_is_seller_rejected(
    client, admin_headers, customer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], status="ACTIVE")

    payload = {
        "listing_id": listing["id"],
        "buyer_id": customer_user["id"],
        "final_price": 500000.0,
    }
    response = client.post("/api/resale-transactions/", json=payload, headers=admin_headers)
    assert response.status_code == 400
    assert "seller cannot be the buyer" in response.json()["detail"].lower()


def test_get_transactions_customer_scoped_to_own(
    client, customer_headers, customer_user, buyer_user
):
    v1 = create_db_vehicle(seller_id=customer_user["id"], registration_number="TN01AA5001", status="approved")
    l1 = create_db_listing(vehicle_id=v1["id"])
    tx1 = create_db_transaction(listing_id=l1["id"], buyer_id=buyer_user["id"], seller_id=customer_user["id"])

    # Third customer transaction
    c3 = create_db_user(email="c3_tx@example.com", phone="9876543241")
    v2 = create_db_vehicle(seller_id=c3["id"], registration_number="TN01AA5002", status="approved")
    l2 = create_db_listing(vehicle_id=v2["id"])
    create_db_transaction(listing_id=l2["id"], buyer_id=buyer_user["id"], seller_id=c3["id"])

    response = client.get("/api/resale-transactions/", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 1
    assert data["transactions"][0]["id"] == tx1["id"]


def test_patch_transaction_admin_update_delivery_notes(
    client, admin_headers, customer_user, buyer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"])
    tx = create_db_transaction(listing_id=listing["id"], buyer_id=buyer_user["id"], seller_id=customer_user["id"])

    response = client.patch(
        f"/api/resale-transactions/{tx['id']}",
        json={"delivery_notes": "Car handed over at residence."},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["delivery_notes"] == "Car handed over at residence."


def test_patch_transaction_cancel_restores_listing_and_vehicle(
    client, admin_headers, customer_user, buyer_user
):
    v = create_db_vehicle(seller_id=customer_user["id"], status="sold")
    listing = create_db_listing(vehicle_id=v["id"], status="SOLD")
    tx = create_db_transaction(
        listing_id=listing["id"],
        buyer_id=buyer_user["id"],
        seller_id=customer_user["id"],
        status="CONFIRMED",
    )

    response = client.patch(
        f"/api/resale-transactions/{tx['id']}",
        json={"status": "CANCELLED"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"

    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM vehicle_listings WHERE id = %s;", (listing["id"],))
            assert cur.fetchone()[0] == "ACTIVE"
            cur.execute("SELECT status FROM vehicles WHERE id = %s;", (v["id"],))
            assert cur.fetchone()[0] == "approved"

