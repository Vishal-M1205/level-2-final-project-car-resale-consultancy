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
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.vehicle_document import VehicleDocument
from app.models.vehicle_inspection import VehicleInspection
from app.models.vehicle_listing import VehicleListing
from sqlalchemy import delete, select


async def cleanup(session):
    # Clean up test records
    await session.execute(
        delete(VehicleListing).where(VehicleListing.listing_description.like("TESTALL%"))
    )
    v_rows = await session.execute(
        select(Vehicle.id).where(Vehicle.registration_number.like("TESTALL%"))
    )
    v_ids = list(v_rows.scalars().all())
    if v_ids:
        await session.execute(
            delete(VehicleDocument).where(VehicleDocument.vehicle_id.in_(v_ids))
        )
        await session.execute(
            delete(VehicleInspection).where(VehicleInspection.vehicle_id.in_(v_ids))
        )
        await session.execute(
            delete(VehicleListing).where(VehicleListing.vehicle_id.in_(v_ids))
        )
        await session.execute(delete(Vehicle).where(Vehicle.id.in_(v_ids)))
    await session.commit()


async def run_all_tests():
    app.state.client = None

    async with AsyncSessionMaker() as session:
        await cleanup(session)

        # Get test users
        admin = (
            await session.execute(select(User).where(User.role == "ADMIN"))
        ).scalars().first()
        consultant = (
            await session.execute(select(User).where(User.role == "CONSULTANT"))
        ).scalars().first()
        seller = (
            await session.execute(select(User).where(User.role == "CUSTOMER"))
        ).scalars().first()

        assert admin, "Admin user must exist"
        assert consultant, "Consultant user must exist"
        assert seller, "Customer/Seller user must exist"

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
        print("  AUTO CONSULTANCY - COMPREHENSIVE END-TO-END AUDIT")
        print("=======================================================")

        # -----------------------------------------------------------
        # 1. VEHICLE SUBMISSION & RETRIEVAL
        # -----------------------------------------------------------
        print("\n[1] Testing Vehicle Submission & Retrieval...")
        vehicle_payload = {
            "brand": "Maruti Suzuki",
            "model": "Swift",
            "variant": "ZXI Plus",
            "registration_number": "TESTALL01",
            "manufacturing_year": 2022,
            "fuel_type": "petrol",
            "transmission": "manual",
            "kilometers_driven": 18000,
            "ownership_count": 1,
            "expected_price": 650000.00,
            "seating_capacity": 5,
            "description": "TESTALL Single owner well maintained car",
        }
        res = await client.post("/api/vehicles/", json=vehicle_payload, headers=seller_headers)
        assert res.status_code == 201, f"Vehicle submission failed: {res.text}"
        vehicle_data = res.json()
        vehicle_id = vehicle_data["id"]
        assert vehicle_data["status"] == "submitted"
        print(f" -> Vehicle created with ID: {vehicle_id}, status: {vehicle_data['status']}")

        # Get Vehicle by ID (Consultant/Admin scope: vehicle:read)
        res = await client.get(f"/api/vehicles/{vehicle_id}", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["registration_number"] == "TESTALL01"
        print(" -> GET /api/vehicles/{id} (Admin) verified.")

        # Get My Vehicles (Customer scope: vehicle:read_own)
        my_res = await client.get("/api/vehicles/my-vehicles", headers=seller_headers)
        assert my_res.status_code == 200
        assert any(v["id"] == vehicle_id for v in my_res.json()["vehicles"])
        print(" -> GET /api/vehicles/my-vehicles (Seller) verified.")

        # Get Vehicles List with Filter (Consultant/Admin scope: vehicle:read)
        res = await client.get("/api/vehicles/?brand=Maruti Suzuki&fuel_type=petrol", headers=admin_headers)
        assert res.status_code == 200
        assert any(v["id"] == vehicle_id for v in res.json()["vehicles"])
        print(" -> GET /api/vehicles/ (Admin with filters) verified.")

        # -----------------------------------------------------------
        # 2. VEHICLE DETAILS UPDATES (PATCH & PUT)
        # -----------------------------------------------------------
        print("\n[2] Testing Vehicle Updates (PATCH & PUT)...")
        # PATCH update
        patch_res = await client.patch(
            f"/api/vehicles/{vehicle_id}",
            json={"kilometers_driven": 19000},
            headers=seller_headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["kilometers_driven"] == 19000
        print(" -> PATCH /api/vehicles/{id} verified.")

        # PUT update (full replacement)
        put_payload = {**vehicle_payload, "expected_price": 640000.00, "kilometers_driven": 19500}
        put_res = await client.put(f"/api/vehicles/{vehicle_id}", json=put_payload, headers=seller_headers)
        assert put_res.status_code == 200
        assert Decimal(str(put_res.json()["expected_price"])) == Decimal("640000.00")
        print(" -> PUT /api/vehicles/{id} verified.")

        # -----------------------------------------------------------
        # 3. VEHICLE DOCUMENT UPLOADS
        # -----------------------------------------------------------
        print("\n[3] Testing Vehicle Document Uploads...")
        for doc_type in ["RC", "INSURANCE", "PUC"]:
            fake_file = io.BytesIO(b"%PDF-1.4 test document content")
            files = {"file": (f"{doc_type}.pdf", fake_file, "application/pdf")}
            data = {"document_type": doc_type}
            upload_res = await client.post(
                f"/api/vehicles/{vehicle_id}/documents",
                data=data,
                files=files,
                headers=seller_headers,
            )
            assert upload_res.status_code == 201, f"Failed to upload {doc_type}: {upload_res.text}"
            print(f" -> Uploaded document: {doc_type}")

        # Get uploaded documents
        docs_res = await client.get(f"/api/vehicles/{vehicle_id}/documents", headers=seller_headers)
        assert docs_res.status_code == 200
        assert len(docs_res.json()) == 3
        print(" -> GET /api/vehicles/{id}/documents verified (all 3 documents present).")

        # -----------------------------------------------------------
        # 4. INSPECTION QUEUE & CLAIM WORKFLOW
        # -----------------------------------------------------------
        print("\n[4] Testing Inspection Queue & Claim...")
        # Get pending unassigned inspections
        pending_res = await client.get("/api/vehicle-inspections/pending", headers=consultant_headers)
        assert pending_res.status_code == 200
        inspections = pending_res.json()["inspections"]
        matching = [i for i in inspections if i["vehicle_id"] == vehicle_id]
        assert len(matching) > 0, "Inspection not found in pending queue"
        inspection_id = matching[0]["id"]
        print(f" -> Found pending inspection ID: {inspection_id}")

        # Claim inspection
        claim_res = await client.post(
            f"/api/vehicle-inspections/{inspection_id}/claim",
            headers=consultant_headers,
        )
        assert claim_res.status_code == 200
        assert claim_res.json()["consultant_id"] == consultant.id
        print(" -> POST /api/vehicle-inspections/{id}/claim verified.")

        # Verify inspection is now in Admin claimed list
        claimed_res = await client.get("/api/vehicle-inspections/claimed", headers=admin_headers)
        assert claimed_res.status_code == 200
        assert any(i["id"] == inspection_id for i in claimed_res.json()["inspections"])
        print(" -> GET /api/vehicle-inspections/claimed (Admin) verified.")

        # Verify inspection appears in Consultant my-inspections
        my_inspec_res = await client.get("/api/vehicle-inspections/my-inspections", headers=consultant_headers)
        assert my_inspec_res.status_code == 200
        assert any(i["id"] == inspection_id for i in my_inspec_res.json()["inspections"])
        print(" -> GET /api/vehicle-inspections/my-inspections verified.")

        # Test Unclaim & Re-claim
        unclaim_res = await client.post(
            f"/api/vehicle-inspections/{inspection_id}/unclaim",
            headers=consultant_headers,
        )
        assert unclaim_res.status_code == 200
        print(" -> POST /api/vehicle-inspections/{id}/unclaim verified.")

        # Re-claim for completing report
        reclaim_res = await client.post(
            f"/api/vehicle-inspections/{inspection_id}/claim",
            headers=consultant_headers,
        )
        assert reclaim_res.status_code == 200

        # -----------------------------------------------------------
        # 5. SUBMIT & UPDATE INSPECTION REPORT (COMPLETE & PUT)
        # -----------------------------------------------------------
        print("\n[5] Testing Inspection Completion & PUT Updates...")
        report_data = {
            "condition": "good",
            "engine_condition": "excellent",
            "exterior_condition": "good",
            "interior_condition": "good",
            "accident_history": False,
            "estimated_market_value": 600000.00,
            "inspection_notes": "Engine and transmission are in top shape.",
        }
        complete_res = await client.patch(
            f"/api/vehicle-inspections/{inspection_id}/complete",
            json=report_data,
            headers=consultant_headers,
        )
        assert complete_res.status_code == 200
        assert complete_res.json()["status"] == "COMPLETED"
        print(" -> PATCH /api/vehicle-inspections/{id}/complete verified.")

        # Get full inspection details
        detail_res = await client.get(f"/api/vehicle-inspections/{inspection_id}", headers=consultant_headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["status"] == "COMPLETED"
        assert len(detail_res.json()["documents"]) == 3
        print(" -> GET /api/vehicle-inspections/{id} verified (includes vehicle & documents).")

        # Get completed inspections list (Admin only)
        completed_res = await client.get("/api/vehicle-inspections/completed", headers=admin_headers)
        assert completed_res.status_code == 200
        assert any(i["id"] == inspection_id for i in completed_res.json()["inspections"])
        print(" -> GET /api/vehicle-inspections/completed verified.")

        # Consultant updates report via PUT while vehicle is submitted
        put_report = {**report_data, "estimated_market_value": 610000.00, "interior_condition": "excellent"}
        put_res = await client.put(
            f"/api/vehicle-inspections/{inspection_id}",
            json=put_report,
            headers=consultant_headers,
        )
        assert put_res.status_code == 200
        assert put_res.json()["interior_condition"] == "excellent"
        print(" -> PUT /api/vehicle-inspections/{id} by Consultant verified.")

        # -----------------------------------------------------------
        # 6. ADMIN DECISION & LISTING CREATION
        # -----------------------------------------------------------
        print("\n[6] Testing Admin Decision & Vehicle Listing Integration...")
        dec_res = await client.patch(
            f"/api/vehicles/{vehicle_id}/decision",
            json={"action": "APPROVED"},
            headers=admin_headers,
        )
        assert dec_res.status_code == 200
        assert dec_res.json()["status"] == "approved"
        print(" -> Admin APPROVED vehicle.")

        # Verify active listing was created in database
        async with AsyncSessionMaker() as session:
            stmt = select(VehicleListing).where(VehicleListing.vehicle_id == vehicle_id)
            listing = (await session.execute(stmt)).scalar_one()
            assert listing.status == "ACTIVE"
            assert listing.listed_price == Decimal("610000.00")
            print(f" -> Active listing verified! Listed Price: Rs. {listing.listed_price}")

        # Verify Consultant is FORBIDDEN to PUT inspection once approved
        forbidden_res = await client.put(
            f"/api/vehicle-inspections/{inspection_id}",
            json=put_report,
            headers=consultant_headers,
        )
        assert forbidden_res.status_code == 403
        print(" -> Consultant PUT on approved vehicle correctly rejected (403 Forbidden).")

        # Admin PUT on approved vehicle -> Updates inspection AND synchronizes listing price!
        admin_put_report = {**put_report, "estimated_market_value": 625000.00}
        admin_put_res = await client.put(
            f"/api/vehicle-inspections/{inspection_id}",
            json=admin_put_report,
            headers=admin_headers,
        )
        assert admin_put_res.status_code == 200

        async with AsyncSessionMaker() as session:
            stmt = select(VehicleListing).where(VehicleListing.vehicle_id == vehicle_id)
            listing = (await session.execute(stmt)).scalar_one()
            assert listing.listed_price == Decimal("625000.00")
            print(f" -> Admin PUT on approved vehicle synchronized listing price to Rs. {listing.listed_price}!")

        # -----------------------------------------------------------
        # 7. REJECTION, RESUBMISSION & CANCELLATION
        # -----------------------------------------------------------
        print("\n[7] Testing Rejection, Admin Resubmit & Cancel...")
        # Admin rejects vehicle -> deactivates listing
        rej_res = await client.patch(
            f"/api/vehicles/{vehicle_id}/decision",
            json={"action": "REJECTED", "rejection_reason": "Price recalibration required"},
            headers=admin_headers,
        )
        assert rej_res.status_code == 200

        async with AsyncSessionMaker() as session:
            stmt = select(VehicleListing).where(VehicleListing.vehicle_id == vehicle_id)
            listing = (await session.execute(stmt)).scalar_one()
            assert listing.status == "INACTIVE"
            print(" -> Rejection correctly set listing to INACTIVE.")

        # Seller attempts to resubmit -> 403 Forbidden
        seller_resub = await client.post(f"/api/vehicles/{vehicle_id}/resubmit", headers=seller_headers)
        assert seller_resub.status_code == 403
        print(" -> Seller resubmit attempt correctly rejected (403 Forbidden).")

        # Admin resubmits vehicle -> status 'submitted', inspection 'PENDING'
        admin_resub = await client.post(f"/api/vehicles/{vehicle_id}/resubmit", headers=admin_headers)
        assert admin_resub.status_code == 200
        assert admin_resub.json()["vehicle_status"] == "submitted"
        assert admin_resub.json()["inspection_status"] == "PENDING"
        print(" -> Admin resubmitted vehicle (status: submitted, inspection: PENDING).")

        # Admin cancels inspection -> vehicle rejected, inspection CANCELLED
        cancel_res = await client.patch(
            f"/api/vehicle-inspections/{inspection_id}/cancel",
            headers=admin_headers,
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["inspection_status"] == "CANCELLED"
        assert cancel_res.json()["vehicle_status"] == "rejected"
        print(" -> Admin cancelled inspection (inspection: CANCELLED, vehicle: rejected).")

        # -----------------------------------------------------------
        # 8. SOFT DELETE (DEACTIVATE)
        # -----------------------------------------------------------
        print("\n[8] Testing Vehicle Soft Delete...")
        del_res = await client.delete(f"/api/vehicles/{vehicle_id}", headers=seller_headers)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deactivated"
        print(" -> Vehicle successfully soft-deleted (status: deactivated).")

        # Final Cleanup
        async with AsyncSessionMaker() as session:
            await cleanup(session)

        print("\n=======================================================")
        print("  ALL 20+ ENDPOINTS & BUSINESS LOGICS VERIFIED 100%!  ")
        print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())