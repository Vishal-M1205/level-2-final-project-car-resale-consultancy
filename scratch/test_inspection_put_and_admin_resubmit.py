import asyncio
import os
import sys
from decimal import Decimal
from httpx import ASGITransport, AsyncClient

sys.path.append(os.getcwd())

from app.database.database import AsyncSessionMaker as AsyncSessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.vehicle_document import VehicleDocument
from app.models.vehicle_inspection import VehicleInspection
from app.models.vehicle_listing import VehicleListing
from sqlalchemy import delete, select


async def cleanup(session):
    await session.execute(
        delete(VehicleListing).where(VehicleListing.listing_description.like("TESTPUT%"))
    )
    v_rows = await session.execute(
        select(Vehicle.id).where(Vehicle.registration_number.like("TESTPUT%"))
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


async def main():
    app.state.client = None
    async with AsyncSessionLocal() as session:
        await cleanup(session)

        # Get test users
        admin = (
            await session.execute(select(User).where(User.role == "ADMIN"))
        ).scalars().first()
        consultant_a = (
            await session.execute(
                select(User).where(User.role == "CONSULTANT").order_by(User.id.asc())
            )
        ).scalars().first()
        consultant_b = (
            await session.execute(
                select(User).where(User.role == "CONSULTANT").order_by(User.id.desc())
            )
        ).scalars().first()
        customer = (
            await session.execute(select(User).where(User.role == "CUSTOMER"))
        ).scalars().first()

        assert admin, "Admin user not found"
        assert consultant_a, "Consultant A not found"
        assert consultant_b, "Consultant B not found"
        assert customer, "Customer user not found"

        admin_token = create_access_token(
            {"sub": admin.email, "role": "ADMIN", "type": "access"}
        )
        consultant_a_token = create_access_token(
            {"sub": consultant_a.email, "role": "CONSULTANT", "type": "access"}
        )
        consultant_b_token = create_access_token(
            {"sub": consultant_b.email, "role": "CONSULTANT", "type": "access"}
        )
        customer_token = create_access_token(
            {"sub": customer.email, "role": "CUSTOMER", "type": "access"}
        )

        # Create a test vehicle
        vehicle = Vehicle(
            seller_id=customer.id,
            brand="Hyundai",
            model="i20",
            manufacturing_year=2021,
            registration_number="TESTPUT01",
            fuel_type="petrol",
            transmission="manual",
            kilometers_driven=25000,
            expected_price=Decimal("450000.00"),
            seating_capacity=5,
            status="submitted",
        )
        session.add(vehicle)
        await session.flush()

        inspection = VehicleInspection(
            vehicle_id=vehicle.id,
            status="PENDING",
            consultant_id=None,
        )
        session.add(inspection)
        await session.commit()
        await session.refresh(vehicle)
        await session.refresh(inspection)
        v_id = vehicle.id
        i_id = inspection.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n--- 1. Testing PUT on PENDING inspection (Should Fail 400) ---")
        put_payload = {
            "condition": "good",
            "engine_condition": "good",
            "exterior_condition": "excellent",
            "interior_condition": "good",
            "accident_history": False,
            "estimated_market_value": 450000.00,
            "inspection_notes": "Initial completed inspection report",
        }
        res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=put_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        print(f"PUT on PENDING inspection status: {res.status_code}")
        assert res.status_code == 400
        assert "Only completed inspections can be updated" in res.json()["detail"]

        print("\n--- 2. Consultant A claims and completes inspection ---")
        claim_res = await client.post(
            f"/api/vehicle-inspections/{i_id}/claim",
            headers={"Authorization": f"Bearer {consultant_a_token}"},
        )
        assert claim_res.status_code == 200, claim_res.text

        comp_res = await client.patch(
            f"/api/vehicle-inspections/{i_id}/complete",
            json=put_payload,
            headers={"Authorization": f"Bearer {consultant_a_token}"},
        )
        assert comp_res.status_code == 200, comp_res.text
        print("Inspection successfully completed by Consultant A.")

        print("\n--- 3. Consultant B attempts to PUT Consultant A's report (Should Fail 403) ---")
        other_payload = {**put_payload, "inspection_notes": "Consultant B hack"}
        res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=other_payload,
            headers={"Authorization": f"Bearer {consultant_b_token}"},
        )
        print(f"Consultant B PUT status: {res.status_code}")
        assert res.status_code == 403

        print("\n--- 4. Consultant A updates their completed report via PUT (Should Succeed 200) ---")
        updated_payload = {
            **put_payload,
            "interior_condition": "excellent",
            "estimated_market_value": 470000.00,
            "inspection_notes": "Corrected interior condition to excellent",
        }
        res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=updated_payload,
            headers={"Authorization": f"Bearer {consultant_a_token}"},
        )
        print(f"Consultant A PUT status: {res.status_code}")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["interior_condition"] == "excellent"
        assert Decimal(str(data["estimated_market_value"])) == Decimal("470000.00")

        print("\n--- 5. Admin updates completed report while submitted (Should Succeed 200) ---")
        admin_payload = {
            **updated_payload,
            "estimated_market_value": 480000.00,
            "inspection_notes": "Admin adjusted estimated market value",
        }
        res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=admin_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        print(f"Admin PUT status: {res.status_code}")
        assert res.status_code == 200
        assert Decimal(str(res.json()["estimated_market_value"])) == Decimal("480000.00")

        print("\n--- 6. Admin approves vehicle, then test consultant & admin PUT on approved vehicle ---")
        # Add required docs to approve
        async with AsyncSessionLocal() as session:
            for dtype in ["RC", "INSURANCE", "PUC"]:
                doc = VehicleDocument(
                    vehicle_id=v_id,
                    document_type=dtype,
                    original_filename=f"{dtype}.pdf",
                    document_url=f"/fake/{dtype}.pdf",
                )
                session.add(doc)
            await session.commit()

        # Approve vehicle
        dec_res = await client.patch(
            f"/api/vehicles/{v_id}/decision",
            json={"action": "APPROVED"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert dec_res.status_code == 200, dec_res.text
        print("Vehicle approved by Admin.")

        # Consultant A tries to edit approved vehicle inspection -> 403 Forbidden!
        res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=updated_payload,
            headers={"Authorization": f"Bearer {consultant_a_token}"},
        )
        print(f"Consultant A PUT after vehicle approved status: {res.status_code}")
        assert res.status_code == 403
        assert "Only administrators can modify an inspection report after the vehicle decision has been made" in res.json()["detail"]

        # Admin edits approved vehicle inspection -> 200 OK!
        admin_approved_payload = {
            **admin_payload,
            "estimated_market_value": 520000.00,
            "inspection_notes": "Admin updated post-approval remarks",
        }
        res = await client.put(
            f"/api/vehicle-inspections/{i_id}",
            json=admin_approved_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        print(f"Admin PUT after vehicle approved status: {res.status_code}")
        assert res.status_code == 200
        assert res.json()["inspection_notes"] == "Admin updated post-approval remarks"

        # Verify that listing.listed_price was automatically updated to 520000.00!
        async with AsyncSessionLocal() as session:
            stmt = select(VehicleListing).where(VehicleListing.vehicle_id == v_id)
            listing = (await session.execute(stmt)).scalar_one()
            print(f"Synchronized listing listed_price: {listing.listed_price}")
            assert listing.listed_price == Decimal("520000.00")

        print("\n--- 7. Test Admin-Only Resubmit ---")
        # Reject the vehicle first so it can be resubmitted
        rej_res = await client.patch(
            f"/api/vehicles/{v_id}/decision",
            json={"action": "REJECTED", "rejection_reason": "Test rejection"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert rej_res.status_code == 200, rej_res.text
        print("Vehicle rejected by Admin.")

        # Customer/Seller tries to resubmit -> 403 Forbidden
        seller_resub = await client.post(
            f"/api/vehicles/{v_id}/resubmit",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        print(f"Customer resubmit status: {seller_resub.status_code}")
        assert seller_resub.status_code == 403, seller_resub.text

        # Admin resubmits -> 200 OK
        admin_resub = await client.post(
            f"/api/vehicles/{v_id}/resubmit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        print(f"Admin resubmit status: {admin_resub.status_code}")
        assert admin_resub.status_code == 200, admin_resub.text
        resub_data = admin_resub.json()
        assert resub_data["vehicle_status"] == "submitted"
        assert resub_data["inspection_status"] == "PENDING"
        print("Vehicle successfully resubmitted by Admin!")

        # Final cleanup
        async with AsyncSessionLocal() as session:
            await cleanup(session)
        print("\nAll PUT and Admin-only Resubmit tests passed with 100% success!")


if __name__ == "__main__":
    asyncio.run(main())
