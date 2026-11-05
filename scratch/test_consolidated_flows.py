import asyncio
import io
import os
import sys
from decimal import Decimal
from httpx import ASGITransport, AsyncClient

sys.path.append(os.getcwd())

from app.core.security import create_access_token
from app.database.database import AsyncSessionMaker
from app.main import app
from app.models.resale_transaction import ResaleTransaction
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.vehicle_document import VehicleDocument
from app.models.vehicle_inspection import VehicleInspection
from app.models.vehicle_listing import VehicleListing
from sqlalchemy import delete, select


async def cleanup(session):
    listing_rows = await session.execute(
        select(VehicleListing.id).where(VehicleListing.listing_description.like("TESTCON%"))
    )
    listing_ids = list(listing_rows.scalars().all())
    if listing_ids:
        await session.execute(
            delete(ResaleTransaction).where(ResaleTransaction.listing_id.in_(listing_ids))
        )
        await session.execute(
            delete(VehicleListing).where(VehicleListing.id.in_(listing_ids))
        )
    v_rows = await session.execute(
        select(Vehicle.id).where(Vehicle.registration_number.like("TESTCON%"))
    )
    v_ids = list(v_rows.scalars().all())
    if v_ids:
        l_rows = await session.execute(
            select(VehicleListing.id).where(VehicleListing.vehicle_id.in_(v_ids))
        )
        l_ids = list(l_rows.scalars().all())
        if l_ids:
            await session.execute(
                delete(ResaleTransaction).where(ResaleTransaction.listing_id.in_(l_ids))
            )
            await session.execute(
                delete(VehicleListing).where(VehicleListing.id.in_(l_ids))
            )
        await session.execute(
            delete(VehicleDocument).where(VehicleDocument.vehicle_id.in_(v_ids))
        )
        await session.execute(
            delete(VehicleInspection).where(VehicleInspection.vehicle_id.in_(v_ids))
        )
        await session.execute(delete(Vehicle).where(Vehicle.id.in_(v_ids)))
    await session.commit()


async def run_consolidated_tests():
    app.state.client = None

    async with AsyncSessionMaker() as session:
        await cleanup(session)

        admin = (
            await session.execute(select(User).where(User.role == "ADMIN"))
        ).scalars().first()
        consultant = (
            await session.execute(select(User).where(User.role == "CONSULTANT"))
        ).scalars().first()
        seller = (
            await session.execute(select(User).where(User.role == "CUSTOMER"))
        ).scalars().first()

        assert admin and consultant and seller, "All 3 roles must exist"

        admin_token = create_access_token(
            {"sub": admin.email, "role": "ADMIN", "type": "access"}
        )
        consultant_token = create_access_token(
            {"sub": consultant.email, "role": "CONSULTANT", "type": "access"}
        )
        seller_token = create_access_token(
            {"sub": seller.email, "role": "CUSTOMER", "type": "access"}
        )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    consultant_headers = {"Authorization": f"Bearer {consultant_token}"}
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n=======================================================")
        print("  CONSOLIDATED ROUTES & LOGIC VERIFICATION AUDIT")
        print("=======================================================")

        # -----------------------------------------------------------
        # 1. VEHICLE SUBMISSION & SMART LISTING
        # -----------------------------------------------------------
        print("\n[1] Testing Vehicle Submission & Unified GET List...")
        vehicle_payload = {
            "brand": "Maruti Suzuki",
            "model": "Swift",
            "variant": "ZXI Plus",
            "registration_number": "TESTCON001",
            "manufacturing_year": 2022,
            "fuel_type": "petrol",
            "transmission": "manual",
            "kilometers_driven": 18000,
            "ownership_count": 1,
            "expected_price": 650000.00,
            "seating_capacity": 5,
            "description": "TESTCON Single owner well maintained car",
        }
        res = await client.post("/api/vehicles/", json=vehicle_payload, headers=seller_headers)
        assert res.status_code == 201, f"Failed: {res.text}"
        v_id = res.json()["id"]
        print(f" -> Vehicle created with ID: {v_id}")

        # Seller views vehicles via GET /api/vehicles/ (automatically scoped to own vehicles)
        res_seller = await client.get("/api/vehicles/", headers=seller_headers)
        assert res_seller.status_code == 200
        assert any(v["id"] == v_id for v in res_seller.json()["vehicles"])
        print(" -> GET /api/vehicles/ (Seller auto-scoped to own) verified.")

        # Admin views all vehicles via GET /api/vehicles/
        res_admin = await client.get("/api/vehicles/?brand=Maruti Suzuki&fuel_type=petrol", headers=admin_headers)
        assert res_admin.status_code == 200
        assert any(v["id"] == v_id for v in res_admin.json()["vehicles"])
        print(" -> GET /api/vehicles/ (Admin with filters) verified.")

        # Seller views single vehicle by ID
        res_single = await client.get(f"/api/vehicles/{v_id}", headers=seller_headers)
        assert res_single.status_code == 200
        assert res_single.json()["id"] == v_id
        print(" -> GET /api/vehicles/{id} (Seller viewing own) verified.")

        # -----------------------------------------------------------
        # 2. VEHICLE UPDATE (SINGLE UNIFIED PATCH)
        # -----------------------------------------------------------
        print("\n[2] Testing Unified PATCH for Vehicle Updates...")
        patch_res = await client.patch(
            f"/api/vehicles/{v_id}",
            json={"expected_price": 640000.00, "kilometers_driven": 19500},
            headers=seller_headers,
        )
        assert patch_res.status_code == 200
        assert Decimal(str(patch_res.json()["expected_price"])) == Decimal("640000.00")
        assert patch_res.json()["kilometers_driven"] == 19500
        print(" -> PATCH /api/vehicles/{id} (Unified update) verified.")

        # -----------------------------------------------------------
        # 3. VEHICLE DOCUMENTS
        # -----------------------------------------------------------
        print("\n[3] Testing Vehicle Documents...")
        for doc_type in ["RC", "INSURANCE", "PUC"]:
            fake_file = io.BytesIO(b"%PDF-1.4 test document content")
            files = {"file": (f"{doc_type}.pdf", fake_file, "application/pdf")}
            data = {"document_type": doc_type}
            upload_res = await client.post(
                f"/api/vehicles/{v_id}/documents",
                data=data,
                files=files,
                headers=seller_headers,
            )
            assert upload_res.status_code == 201

        docs_res = await client.get(f"/api/vehicles/{v_id}/documents", headers=seller_headers)
        assert docs_res.status_code == 200
        assert len(docs_res.json()) == 3
        print(" -> Uploaded and retrieved 3 documents.")

        # -----------------------------------------------------------
        # 4. UNIFIED INSPECTIONS LIST & CLAIM
        # -----------------------------------------------------------
        print("\n[4] Testing Unified GET /api/vehicle-inspections/...")
        # Get unassigned pending inspections (replaces /pending)
        res_unassigned = await client.get(
            "/api/vehicle-inspections/?status=PENDING&is_claimed=false",
            headers=consultant_headers,
        )
        assert res_unassigned.status_code == 200
        matching = [i for i in res_unassigned.json()["inspections"] if i["vehicle_id"] == v_id]
        assert len(matching) > 0
        i_id = matching[0]["id"]
        print(f" -> Found unassigned pending inspection ID: {i_id}")

        # Claim inspection
        claim_res = await client.post(f"/api/vehicle-inspections/{i_id}/claim", headers=consultant_headers)
        assert claim_res.status_code == 200
        print(" -> Claimed inspection.")

        # Admin checks claimed queue (replaces /claimed)
        res_claimed = await client.get(
            "/api/vehicle-inspections/?status=PENDING&is_claimed=true",
            headers=admin_headers,
        )
        assert res_claimed.status_code == 200
        assert any(i["id"] == i_id for i in res_claimed.json()["inspections"])
        print(" -> Claimed queue filtered via unified GET verified.")

        # Consultant checks own inspections (replaces /my-inspections)
        res_mine = await client.get(
            "/api/vehicle-inspections/?mine=true",
            headers=consultant_headers,
        )
        assert res_mine.status_code == 200
        assert any(i["id"] == i_id for i in res_mine.json()["inspections"])
        print(" -> Consultant's own queue filtered via unified GET verified.")

        # -----------------------------------------------------------
        # 5. UNIFIED PUT FOR REPORT SUBMISSION & UPDATES
        # -----------------------------------------------------------
        print("\n[5] Testing Unified PUT for Report Submission & Updates...")
        report_data = {
            "condition": "good",
            "engine_condition": "excellent",
            "exterior_condition": "good",
            "interior_condition": "good",
            "accident_history": False,
            "estimated_market_value": 600000.00,
            "inspection_notes": "Engine and transmission are in top shape.",
        }
        # Initial submission via PUT (replaces /complete)
        submit_res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=report_data,
            headers=consultant_headers,
        )
        assert submit_res.status_code == 200
        assert submit_res.json()["status"] == "COMPLETED"
        print(" -> Report submitted via PUT /{id} -> status: COMPLETED.")

        # Admin views completed list via unified GET (replaces /completed)
        res_completed = await client.get(
            "/api/vehicle-inspections/?status=COMPLETED",
            headers=admin_headers,
        )
        assert res_completed.status_code == 200
        assert any(i["id"] == i_id for i in res_completed.json()["inspections"])
        print(" -> Completed inspections filtered via unified GET verified.")

        # Consultant updates report details via same PUT /{id}
        put_update = {**report_data, "interior_condition": "excellent", "estimated_market_value": 615000.00}
        put_res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=put_update,
            headers=consultant_headers,
        )
        assert put_res.status_code == 200
        assert put_res.json()["interior_condition"] == "excellent"
        print(" -> Report updated via PUT /{id} verified.")

        # -----------------------------------------------------------
        # 6. ADMIN DECISION & UNIFIED RESUBMIT
        # -----------------------------------------------------------
        print("\n[6] Testing Admin Decision (APPROVED, REJECTED, RESUBMIT)...")
        # Approve
        app_res = await client.patch(
            f"/api/vehicles/{v_id}/decision",
            json={"action": "APPROVED"},
            headers=admin_headers,
        )
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "approved"
        print(" -> Admin APPROVED vehicle.")

        # Reject
        rej_res = await client.patch(
            f"/api/vehicles/{v_id}/decision",
            json={"action": "REJECTED", "rejection_reason": "Price adjustment needed"},
            headers=admin_headers,
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["status"] == "rejected"
        print(" -> Admin REJECTED vehicle.")

        # Unified Resubmit via action: "RESUBMIT" (replaces POST /resubmit)
        resub_res = await client.patch(
            f"/api/vehicles/{v_id}/decision",
            json={"action": "RESUBMIT"},
            headers=admin_headers,
        )
        assert resub_res.status_code == 200
        assert resub_res.json()["status"] == "submitted"
        print(" -> Admin RESUBMITTED vehicle via unified decision endpoint.")

        # Cancel inspection
        cancel_res = await client.patch(
            f"/api/vehicle-inspections/{i_id}/cancel",
            headers=admin_headers,
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["inspection_status"] == "CANCELLED"
        print(" -> Admin cancelled inspection.")

        # Soft delete vehicle
        del_res = await client.delete(f"/api/vehicles/{v_id}", headers=seller_headers)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deactivated"
        print(" -> Vehicle soft deleted.")

        # Cleanup
        async with AsyncSessionMaker() as session:
            await cleanup(session)

        print("\n=======================================================")
        print("  ALL CONSOLIDATED ROUTES PASSED WITH 100% SUCCESS!    ")
        print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_consolidated_tests())

