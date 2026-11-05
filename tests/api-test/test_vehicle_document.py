import io
import shutil
from pathlib import Path
import pytest
from tests.conftest import create_db_vehicle


@pytest.fixture(autouse=True)
def cleanup_uploads():
    yield
    upload_path = Path("uploads")
    if upload_path.exists():
        shutil.rmtree(upload_path, ignore_errors=True)


def create_dummy_pdf():
    return (
        "test_doc.pdf",
        io.BytesIO(b"%PDF-1.4 test document content for automated testing"),
        "application/pdf",
    )


def test_upload_document_success(client, customer_user, customer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    filename, file_content, content_type = create_dummy_pdf()
    response = client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "RC"},
        files={"file": (filename, file_content, content_type)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["vehicle_id"] == vehicle["id"]
    assert data["document_type"] == "RC"
    assert "document_url" in data


def test_upload_document_replace_existing(client, customer_user, customer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")

    # Upload first
    client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "INSURANCE"},
        files={"file": create_dummy_pdf()},
    )
    # Upload replacement
    res = client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "INSURANCE"},
        files={"file": ("updated_insurance.pdf", io.BytesIO(b"%PDF-1.4 replacement"), "application/pdf")},
    )
    assert res.status_code == 201
    assert res.json()["original_filename"] == "updated_insurance.pdf"


def test_upload_document_invalid_type(client, customer_user, customer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    response = client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "INVALID_TYPE"},
        files={"file": create_dummy_pdf()},
    )
    assert response.status_code == 400


def test_upload_document_non_pdf_rejected(client, customer_user, customer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    response = client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "RC"},
        files={"file": ("document.txt", io.BytesIO(b"Plain text"), "text/plain")},
    )
    assert response.status_code == 400
    assert "only pdf" in response.json()["detail"].lower()


def test_upload_document_unauthorized_customer(client, customer_user, buyer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    response = client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=buyer_headers,
        data={"document_type": "RC"},
        files={"file": create_dummy_pdf()},
    )
    assert response.status_code == 403


def test_get_vehicle_documents_success(client, customer_user, customer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "RC"},
        files={"file": create_dummy_pdf()},
    )

    response = client.get(f"/api/vehicles/{vehicle['id']}/documents", headers=customer_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["document_type"] == "RC"


def test_delete_vehicle_document_success(client, customer_user, customer_headers):
    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "RC"},
        files={"file": create_dummy_pdf()},
    )

    response = client.delete(
        f"/api/vehicles/{vehicle['id']}/documents/RC",
        headers=customer_headers,
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()


def test_delete_vehicle_document_when_vehicle_approved_rejected(
    client, customer_user, customer_headers
):
    import psycopg
    from tests.conftest import config

    vehicle = create_db_vehicle(seller_id=customer_user["id"], status="submitted")
    client.post(
        f"/api/vehicles/{vehicle['id']}/documents",
        headers=customer_headers,
        data={"document_type": "RC"},
        files={"file": create_dummy_pdf()},
    )

    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE vehicles SET status = 'approved' WHERE id = %s", (vehicle["id"],))

    response = client.delete(
        f"/api/vehicles/{vehicle['id']}/documents/RC",
        headers=customer_headers,
    )
    assert response.status_code == 400

