import os
import sys
from decimal import Decimal
import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import config
from app.core.security import create_access_token, hash_password
from app.database.database import conn_url, get_db_connection
from app.main import app

test_conn_url = conn_url.set(database="car_resale_consultancy_test")
test_engine = create_async_engine(url=test_conn_url, poolclass=NullPool)
TestSession = async_sessionmaker(bind=test_engine, expire_on_commit=False)


async def get_test_session():
    async with TestSession() as session:
        yield session


def _truncate_db():
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE users, vehicles, vehicle_listings, vehicle_inspections, resale_transactions, vehicle_documents RESTART IDENTITY CASCADE;"
            )


from contextlib import asynccontextmanager

@asynccontextmanager
async def dummy_lifespan(app):
    app.state.client = None
    yield

app.router.lifespan_context = dummy_lifespan


@pytest.fixture(autouse=True)
def db_cleanup():
    _truncate_db()
    yield
    _truncate_db()


@pytest.fixture(autouse=True)
def mock_mailjet(monkeypatch):
    async def fake_send_mail(self, payload):
        return None

    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_mail", fake_send_mail
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_db_connection] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =====================================================================
# SEED HELPERS
# =====================================================================


def create_db_user(
    name: str = "Test User",
    email: str = "test@example.com",
    password: str = "Password@123",
    phone: str = "9876543210",
    role: str = "CUSTOMER",
    is_active: bool = True,
) -> dict:
    pwd_hash = hash_password(password)
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, hashed_password, phone, age, gender, address_line_1, district, state, pincode, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, email, phone, role, is_active;
                """,
                (
                    name,
                    email,
                    pwd_hash,
                    phone,
                    25,
                    "MALE",
                    "123 Main St",
                    "Coimbatore",
                    "Tamil Nadu",
                    "641001",
                    role,
                    is_active,
                ),
            )
            row = cur.fetchone()
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "role": row[4],
                "is_active": row[5],
            }


def create_db_vehicle(
    seller_id: int,
    registration_number: str = "TN01AB1234",
    brand: str = "Maruti",
    model: str = "Swift",
    status: str = "submitted",
    expected_price: float = 600000.0,
) -> dict:
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vehicles (seller_id, brand, model, registration_number, manufacturing_year, fuel_type, transmission, kilometers_driven, ownership_count, expected_price, seating_capacity, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, seller_id, brand, model, registration_number, status;
                """,
                (
                    seller_id,
                    brand,
                    model,
                    registration_number,
                    2021,
                    "PETROL",
                    "MANUAL",
                    25000,
                    1,
                    Decimal(str(expected_price)),
                    5,
                    status,
                ),
            )
            row = cur.fetchone()
            return {
                "id": row[0],
                "seller_id": row[1],
                "brand": row[2],
                "model": row[3],
                "registration_number": row[4],
                "status": row[5],
            }


def create_db_inspection(
    vehicle_id: int,
    consultant_id: int | None = None,
    status: str = "PENDING",
    estimated_market_value: float = 580000.0,
) -> dict:
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vehicle_inspections (vehicle_id, consultant_id, status, condition, engine_condition, exterior_condition, interior_condition, accident_history, estimated_market_value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, vehicle_id, consultant_id, status;
                """,
                (
                    vehicle_id,
                    consultant_id,
                    status,
                    "good" if status == "COMPLETED" else None,
                    "good" if status == "COMPLETED" else None,
                    "good" if status == "COMPLETED" else None,
                    "good" if status == "COMPLETED" else None,
                    False,
                    Decimal(str(estimated_market_value)) if status == "COMPLETED" else None,
                ),
            )
            row = cur.fetchone()
            return {
                "id": row[0],
                "vehicle_id": row[1],
                "consultant_id": row[2],
                "status": row[3],
            }


def create_db_listing(
    vehicle_id: int,
    listed_price: float = 580000.0,
    status: str = "ACTIVE",
    description: str = "Well maintained vehicle",
) -> dict:
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vehicle_listings (vehicle_id, listed_price, status, listing_description)
                VALUES (%s, %s, %s, %s)
                RETURNING id, vehicle_id, listed_price, status;
                """,
                (vehicle_id, Decimal(str(listed_price)), status, description),
            )
            row = cur.fetchone()
            return {
                "id": row[0],
                "vehicle_id": row[1],
                "listed_price": row[2],
                "status": row[3],
            }


def create_db_transaction(
    listing_id: int,
    buyer_id: int,
    seller_id: int,
    final_price: float = 570000.0,
    status: str = "CONFIRMED",
    consultant_id: int | None = None,
) -> dict:
    with psycopg.connect(
        host=config.database_host,
        port=config.database_port,
        user=config.database_user,
        password=config.database_password,
        dbname="car_resale_consultancy_test",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resale_transactions (listing_id, buyer_id, seller_id, consultant_id, final_price, status, delivery_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, listing_id, buyer_id, seller_id, final_price, status;
                """,
                (
                    listing_id,
                    buyer_id,
                    seller_id,
                    consultant_id,
                    Decimal(str(final_price)),
                    status,
                    "Delivered with keys",
                ),
            )
            row = cur.fetchone()
            return {
                "id": row[0],
                "listing_id": row[1],
                "buyer_id": row[2],
                "seller_id": row[3],
                "final_price": row[4],
                "status": row[5],
            }


# =====================================================================
# USER FIXTURES
# =====================================================================


@pytest.fixture
def admin_user():
    return create_db_user(
        name="Admin User",
        email="admin@example.com",
        password="AdminPassword@123",
        phone="9999999999",
        role="ADMIN",
    )


@pytest.fixture
def admin_token(admin_user):
    return create_access_token({"sub": admin_user["email"], "role": "ADMIN"})


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def consultant_user():
    return create_db_user(
        name="Consultant User",
        email="consultant@example.com",
        password="Consultant@123",
        phone="9888888888",
        role="CONSULTANT",
    )


@pytest.fixture
def consultant_token(consultant_user):
    return create_access_token({"sub": consultant_user["email"], "role": "CONSULTANT"})


@pytest.fixture
def consultant_headers(consultant_token):
    return {"Authorization": f"Bearer {consultant_token}"}


@pytest.fixture
def customer_user():
    return create_db_user(
        name="Customer Seller",
        email="seller@example.com",
        password="Customer@123",
        phone="9777777777",
        role="CUSTOMER",
    )


@pytest.fixture
def customer_token(customer_user):
    return create_access_token({"sub": customer_user["email"], "role": "CUSTOMER"})


@pytest.fixture
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture
def buyer_user():
    return create_db_user(
        name="Customer Buyer",
        email="buyer@example.com",
        password="Customer@123",
        phone="9666666666",
        role="CUSTOMER",
    )


@pytest.fixture
def buyer_token(buyer_user):
    return create_access_token({"sub": buyer_user["email"], "role": "CUSTOMER"})


@pytest.fixture
def buyer_headers(buyer_token):
    return {"Authorization": f"Bearer {buyer_token}"}


def create_auth_headers(email: str, role: str) -> dict:
    token = create_access_token({"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}

