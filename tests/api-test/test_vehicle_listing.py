from tests.conftest import (
    create_db_listing,
    create_db_vehicle,
)


def test_get_listings_success(client, customer_user, customer_headers):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    create_db_listing(vehicle_id=v["id"], listed_price=600000.0, status="ACTIVE")

    response = client.get("/api/listings/", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["total_listings"] >= 1


def test_get_listings_with_brand_filter(client, customer_user, customer_headers):
    v1 = create_db_vehicle(
        seller_id=customer_user["id"],
        brand="Hyundai",
        model="i20",
        registration_number="TN01AA1001",
        status="approved",
    )
    create_db_listing(vehicle_id=v1["id"], listed_price=450000.0, status="ACTIVE")

    response = client.get("/api/listings/?brand=Hyundai", headers=customer_headers)
    assert response.status_code == 200
    assert len(response.json()["listings"]) >= 1
    assert response.json()["listings"][0]["vehicle"]["brand"] == "Hyundai"


def test_get_listing_by_id_success(client, customer_user, customer_headers):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], listed_price=550000.0)

    response = client.get(f"/api/listings/{listing['id']}", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["id"] == listing["id"]


def test_patch_listing_admin_success(client, admin_headers, customer_user):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], listed_price=500000.0, status="ACTIVE")

    patch_payload = {
        "status": "INACTIVE",
        "listed_price": 520000.0,
        "listing_description": "Updated listing description",
    }
    response = client.patch(
        f"/api/listings/{listing['id']}",
        json=patch_payload,
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "INACTIVE"
    assert float(response.json()["listed_price"]) == 520000.0


def test_patch_listing_customer_forbidden(client, customer_headers, customer_user):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"])

    response = client.patch(
        f"/api/listings/{listing['id']}",
        json={"listed_price": 530000.0},
        headers=customer_headers,
    )
    assert response.status_code == 403


def test_patch_listing_reject_manual_sold(client, admin_headers, customer_user):
    v = create_db_vehicle(seller_id=customer_user["id"], status="approved")
    listing = create_db_listing(vehicle_id=v["id"], status="ACTIVE")

    response = client.patch(
        f"/api/listings/{listing['id']}",
        json={"status": "SOLD"},
        headers=admin_headers,
    )
    assert response.status_code == 422
    assert "cannot manually set status to 'sold'" in response.text.lower()

