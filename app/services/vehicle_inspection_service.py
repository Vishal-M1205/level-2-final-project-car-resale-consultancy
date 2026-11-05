from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User
from app.models.vehicle_inspection import VehicleInspection
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.vehicle_inspection import (
    CustomerInspectionFilterParams,
    InspectionFilterParams,
    VehicleInspectionDetailSubmission,
)
from app.services.email_service import EmailService


class VehicleInspectionService:
    def __init__(
        self,
        session: AsyncSession,
        vehicle_inspection_repository: VehicleInspectionInterface,
        vehicle_repository: VehicleInterface,
        user_repository: UserInterface,
        email_service: EmailService,
        vehicle_listing_repository: VehicleListingInterface | None = None,
    ):
        self.session = session
        self.vehicle_inspection_repository = vehicle_inspection_repository
        self.vehicle_repository = vehicle_repository
        self.user_repository = user_repository
        self.email_service = email_service
        self.vehicle_listing_repository = vehicle_listing_repository

    def _claim_success_payload(self, consultant: User, inspection_id: int, vehicle_id: int) -> dict:
        return {
            "Messages": [
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": consultant.email,
                            "Name": consultant.name,
                        }
                    ],
                    "Subject": f"Inspection Assignment Confirmed - Inspection #{inspection_id}",
                    "HTMLPart": f"""
                        <h2>Vehicle Inspection Claimed Successfully</h2>
                        <p>Hello <strong>{consultant.name}</strong> (Consultant ID: <strong>{consultant.id}</strong>),</p>
                        <p>You have successfully claimed the inspection task for <strong>Vehicle #{vehicle_id}</strong> (Inspection ID: <strong>#{inspection_id}</strong>).</p>
                        <p><strong>Next Steps:</strong></p>
                        <ul>
                            <li>Coordinate with the seller or visit the vehicle location.</li>
                            <li>Perform the vehicle physical inspection (engine, exterior, interior, condition).</li>
                            <li>Submit the completed inspection report with your market value estimate.</li>
                        </ul>
                        <p>Thank you,<br/>Auto Consultancy Management System</p>
                    """,
                }
            ]
        }

    async def claim_vehicle_inspection(self, inspection_id: int, consultant: User) -> dict:
        """
        Assigns an unassigned pending inspection to the calling consultant.
        Guards: prevents double-claiming, verifies vehicle is active, and runs atomically.
        """
        async with self.session.begin():
            existing_inspection = await self.vehicle_inspection_repository.get_inspection_by_id(
                inspection_id
            )

            if not existing_inspection:
                raise NotFoundException("Inspection not found")

            if existing_inspection.consultant_id == consultant.id:
                raise ConflictException("You have already claimed this inspection")

            if existing_inspection.consultant_id is not None:
                raise ConflictException("Inspection is already claimed by another consultant")

            if existing_inspection.status != "PENDING":
                raise ConflictException("Inspection is not in pending status")

            vehicle = await self.vehicle_repository.get_vehicle_by_id(
                existing_inspection.vehicle_id
            )
            if vehicle and vehicle.status == "deactivated":
                raise BadRequestException("Cannot claim inspection for a deactivated vehicle")

            claimed_inspection = await self.vehicle_inspection_repository.claim_inspection(
                inspection_id=inspection_id, consultant_id=consultant.id
            )

            if not claimed_inspection:
                raise ConflictException(
                    "Failed to claim inspection. It may have just been claimed by another consultant."
                )

            vehicle_id = claimed_inspection.vehicle_id

        payload = self._claim_success_payload(
            consultant=consultant,
            inspection_id=inspection_id,
            vehicle_id=vehicle_id,
        )
        if self.email_service:
            try:
                await self.email_service.send_mail(payload)
            except Exception:
                pass

        return {
            "consultant_id": consultant.id,
            "consultant_name": consultant.name,
            "vehicle_id": vehicle_id,
        }

    async def unclaim_vehicle_inspection(self, inspection_id: int, user: User) -> dict:
        """
        Unclaim an inspection.
        Consultant can unclaim their own claimed pending inspection.
        Admin can unclaim any claimed pending inspection.
        Resets consultant_id to None and returns task to the pending pool.
        """
        async with self.session.begin():
            existing_inspection = await self.vehicle_inspection_repository.get_inspection_by_id(
                inspection_id
            )
            if not existing_inspection:
                raise NotFoundException("Inspection not found")

            if existing_inspection.consultant_id is None:
                raise BadRequestException("Inspection is not currently claimed")

            if user.role != "ADMIN" and existing_inspection.consultant_id != user.id:
                raise ForbiddenException("You can only unclaim an inspection claimed by you")

            if existing_inspection.status == "COMPLETED":
                raise BadRequestException(
                    "Cannot unclaim an inspection that has already been completed"
                )

            if existing_inspection.status == "CANCELLED":
                raise BadRequestException("Cannot unclaim a cancelled inspection")

            await self.vehicle_inspection_repository.unclaim_inspection(inspection_id)

            return {
                "inspection_id": inspection_id,
                "vehicle_id": existing_inspection.vehicle_id,
                "status": "PENDING",
                "message": "Inspection successfully unclaimed and returned to pending pool",
            }

    async def cancel_vehicle_inspection(self, inspection_id: int, user: User) -> dict:
        """
        Cancel an inspection.
        Admin only.
        Marks inspection as CANCELLED, rejects vehicle, and deactivates any active listing.
        """
        if user.role != "ADMIN":
            raise ForbiddenException("Only Admins are authorized to cancel an inspection")

        async with self.session.begin():
            existing_inspection = await self.vehicle_inspection_repository.get_inspection_by_id(
                inspection_id
            )
            if not existing_inspection:
                raise NotFoundException("Inspection not found")

            if existing_inspection.status != "PENDING":
                raise BadRequestException(
                    f"Cannot cancel an inspection that is in '{existing_inspection.status}' status. Only pending inspections can be cancelled."
                )

            vehicle = await self.vehicle_repository.get_vehicle_by_id(
                existing_inspection.vehicle_id
            )
            if not vehicle:
                raise NotFoundException("Vehicle not found")

            if vehicle.status == "sold":
                raise BadRequestException(
                    "Cannot cancel inspection for a vehicle that has already been sold"
                )

            if vehicle.status == "deactivated":
                raise BadRequestException("Cannot cancel inspection for a deactivated vehicle")

            await self.vehicle_inspection_repository.cancel_inspection(inspection_id)
            await self.vehicle_repository.update_vehicle_status(vehicle.id, "rejected")

            return {
                "inspection_id": inspection_id,
                "vehicle_id": vehicle.id,
                "inspection_status": "CANCELLED",
                "vehicle_status": "rejected",
                "message": "Inspection has been cancelled and vehicle rejected.",
            }

    async def get_all_inspections(
        self, filters: InspectionFilterParams, current_user: User
    ) -> dict:
        if current_user.role == "CUSTOMER":
            raise ForbiddenException(
                "Customers are not authorized to view the general inspection queue. Please use /api/vehicle-inspections/my-inspections."
            )

        consultant_id: int | None = None
        if current_user.role == "CONSULTANT":
            if filters.mine:
                consultant_id = current_user.id
            elif filters.consultant_id is not None:
                if filters.consultant_id != current_user.id:
                    raise ForbiddenException(
                        "Consultants can only filter by their own consultant ID."
                    )
                consultant_id = current_user.id
        elif current_user.role == "ADMIN":
            consultant_id = filters.consultant_id

        async with self.session.begin():
            return await self.vehicle_inspection_repository.get_inspections(
                filters=filters, consultant_id=consultant_id
            )

    async def get_customer_inspections(
        self, filters: CustomerInspectionFilterParams, current_user: User
    ) -> dict:
        async with self.session.begin():
            return await self.vehicle_inspection_repository.get_inspections(
                filters=filters, seller_id=current_user.id
            )

    async def get_inspection_with_details(self, inspection_id: int, current_user: User) -> dict:
        async with self.session.begin():
            inspection = await self.vehicle_inspection_repository.get_inspection_with_details(
                inspection_id
            )

            if not inspection:
                raise NotFoundException("Inspection not found")

            if current_user.role != "ADMIN":
                if (
                    current_user.role == "CONSULTANT"
                    and inspection.consultant_id == current_user.id
                ):
                    pass
                elif (
                    current_user.role == "CUSTOMER"
                    and inspection.vehicle
                    and inspection.vehicle.seller_id == current_user.id
                ):
                    pass
                else:
                    raise ForbiddenException(
                        "You are not authorized to view an inspection assigned to another consultant"
                    )

            inspection.documents = inspection.vehicle.documents if inspection.vehicle else []
            return inspection

    async def replace_vehicle_inspection(
        self,
        inspection_id: int,
        report_data: VehicleInspectionDetailSubmission,
        user: User,
    ) -> VehicleInspection:
        """
        Handles the dual-purpose report endpoint (PUT):
        - Initial submission (PENDING): moves status to COMPLETED and sets market valuation.
        - Subsequent update (COMPLETED): consultants can update while vehicle is 'submitted';
          once vehicle is 'approved' or 'rejected', only Admins can modify the report.
        - Price sync: if vehicle is already approved, automatically syncs the listed price.
        """
        async with self.session.begin():
            inspection = await self.vehicle_inspection_repository.get_inspection_by_id(
                inspection_id
            )
            if not inspection:
                raise NotFoundException("Inspection not found")

            if inspection.status == "CANCELLED":
                raise BadRequestException("Cannot submit or update a cancelled inspection report.")

            vehicle = await self.vehicle_repository.get_vehicle_by_id(inspection.vehicle_id)
            if not vehicle:
                raise NotFoundException("Associated vehicle not found")

            if vehicle.status in ("sold", "deactivated"):
                raise BadRequestException(
                    f"Cannot update inspection for a vehicle in '{vehicle.status}' status."
                )

            # Initial report submission: requires claimed consultant assignment
            if inspection.status == "PENDING":
                if inspection.consultant_id is None:
                    raise BadRequestException(
                        "This inspection must be claimed before submitting a report."
                    )
                if user.role != "ADMIN" and inspection.consultant_id != user.id:
                    raise ForbiddenException(
                        "You are not authorized to submit a report for an inspection claimed by another consultant."
                    )
                return await self.vehicle_inspection_repository.submit_inspection_report(
                    inspection_id=inspection_id,
                    report_data=report_data,
                )

            if vehicle.status == "submitted":
                if user.role != "ADMIN" and inspection.consultant_id != user.id:
                    raise ForbiddenException(
                        "You are not authorized to update an inspection assigned to another consultant."
                    )
            elif vehicle.status in ("approved", "rejected"):
                if user.role != "ADMIN":
                    raise ForbiddenException(
                        "Only administrators can modify an inspection report after the vehicle decision has been made."
                    )

            updated_inspection = await self.vehicle_inspection_repository.update_inspection_details(
                inspection_id=inspection_id,
                report_data=report_data,
            )

            # Price synchronization: keep active listing price in sync with latest valuation
            if vehicle.status == "approved" and self.vehicle_listing_repository:
                await self.vehicle_listing_repository.update_listing_price(
                    vehicle_id=vehicle.id,
                    listed_price=report_data.estimated_market_value,
                )

            return updated_inspection
