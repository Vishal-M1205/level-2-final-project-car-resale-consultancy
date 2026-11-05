from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOCUMENT_TYPES
from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_document_interface import (
    VehicleDocumentInterface,
)
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.vehicle import (
    VehicleDecisionRequest,
    VehicleDecisionResponse,
    VehicleFilterParams,
    VehicleSubmission,
    VehicleUpdate,
)
from app.services.email_service import EmailService


class VehicleService:
    def __init__(
        self,
        session: AsyncSession,
        vehicle_repository: VehicleInterface,
        vehicle_inspection_repository: VehicleInspectionInterface,
        vehicle_document_repository: VehicleDocumentInterface | None = None,
        vehicle_listing_repository: VehicleListingInterface | None = None,
        user_repository: UserInterface | None = None,
        email_service: EmailService | None = None,
    ):
        self.session = session
        self.vehicle_repository = vehicle_repository
        self.vehicle_inspection_repository = vehicle_inspection_repository
        self.vehicle_document_repository = vehicle_document_repository
        self.vehicle_listing_repository = vehicle_listing_repository
        self.user_repository = user_repository
        self.email_service = email_service

    async def submit_vehicle_details(
        self, vehicle_details: VehicleSubmission, seller_id: int
    ) -> Vehicle:
        async with self.session.begin():
            existing_vehicle = (
                await self.vehicle_repository.get_vehicle_by_registration_number(
                    vehicle_details.registration_number
                )
            )

            if existing_vehicle:
                raise ConflictException(
                    "Vehicle with this registration number already found"
                )

            submitted_vehicle = await self.vehicle_repository.insert_vehicle_details(
                vehicle_details, seller_id
            )

            await self.vehicle_inspection_repository.create_pending_inspection(
                submitted_vehicle.id
            )

            return submitted_vehicle

    async def get_vehicle_by_id(self, vehicle_id: int, user: User) -> Vehicle:
        async with self.session.begin():
            vehicle_details = await self.vehicle_repository.get_vehicle_by_id(
                vehicle_id
            )

            if not vehicle_details:
                raise NotFoundException("No Vehicle found")

            if user.role == "CUSTOMER" and vehicle_details.seller_id != user.id:
                raise ForbiddenException(
                    "You do not have permission to view this vehicle."
                )

            return vehicle_details

    async def get_all_vehicles(self, filters: VehicleFilterParams, user: User) -> dict:
        async with self.session.begin():
            seller_id = user.id if user.role == "CUSTOMER" else filters.seller_id
            return await self.vehicle_repository.get_vehicles(
                filters=filters, seller_id=seller_id
            )

    async def update_vehicle_details(
        self,
        vehicle_id: int,
        update_data: VehicleUpdate,
        user: User,
    ) -> Vehicle:
        """
        Update vehicle details.
        Seller can ONLY update when vehicle status is 'submitted'.
        Admin can update vehicle at ANY status.
        If description is updated and vehicle status is 'approved',
        updates the description in vehicle_listings.listing_description.
        """
        update_fields = update_data.model_dump(exclude_unset=True)
        if not update_fields:
            raise BadRequestException("No fields provided to update.")

        async with self.session.begin():
            vehicle = await self.vehicle_repository.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                raise NotFoundException("Vehicle not found.")

            if vehicle.status == "sold":
                raise BadRequestException(
                    "Cannot edit details for a vehicle that has already been sold."
                )

            if vehicle.status == "deactivated":
                raise BadRequestException(
                    "Cannot edit details for a deactivated vehicle."
                )

            # sellers can only update their own vehicles
            if user.role != "ADMIN":
                if vehicle.seller_id != user.id:
                    raise ForbiddenException(
                        "You do not have permission to update this vehicle."
                    )

                if vehicle.status != "submitted":
                    raise BadRequestException(
                        f"Cannot edit vehicle. Details can only be updated while status is 'submitted' (current status: '{vehicle.status}')."
                    )

            if "registration_number" in update_fields:
                new_reg = update_fields["registration_number"]
                if new_reg != vehicle.registration_number:
                    existing = await self.vehicle_repository.get_vehicle_by_registration_number(
                        new_reg
                    )
                    if existing:
                        raise ConflictException(
                            "A vehicle with this registration number already exists."
                        )

            updated_vehicle = await self.vehicle_repository.update_vehicle_details(
                vehicle_id=vehicle_id,
                update_data=update_fields,
            )

            # update listing description if vehicle is approved and description was updated
            if "description" in update_fields and vehicle.status == "approved":
                new_desc = update_fields["description"] or "No description is mentioned"
                await self.vehicle_listing_repository.update_listing_description(
                    vehicle_id=vehicle_id,
                    description=new_desc,
                )

            return updated_vehicle

    def _approval_email_payload(
        self, seller: User, vehicle: Vehicle, listed_price: Decimal
    ) -> dict:
        return {
            "Messages": [
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": seller.email,
                            "Name": seller.name,
                        }
                    ],
                    "Subject": f"Vehicle Approved & Listed for Resale - {vehicle.registration_number}",
                    "HTMLPart": f"""
                        <h2>Congratulations {seller.name}!</h2>
                        <p>Your vehicle <strong>{vehicle.brand} {vehicle.model}</strong> (Reg No: <strong>{vehicle.registration_number}</strong>) has been <strong>APPROVED</strong> after inspection and document verification.</p>
                        <p>It is now actively listed for resale on our platform at <strong>Rs. {listed_price:,.2f}</strong>.</p>
                        <br/>
                        <p>Best regards,<br/>Auto Consultancy Team</p>
                    """,
                }
            ]
        }

    def _rejection_email_payload(
        self, seller: User, vehicle: Vehicle, reason: str
    ) -> dict:
        return {
            "Messages": [
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": seller.email,
                            "Name": seller.name,
                        }
                    ],
                    "Subject": f"Vehicle Submission Update - {vehicle.registration_number}",
                    "HTMLPart": f"""
                        <h2>Vehicle Inspection Update</h2>
                        <p>Hello {seller.name},</p>
                        <p>Thank you for submitting your vehicle <strong>{vehicle.brand} {vehicle.model}</strong> (Reg No: <strong>{vehicle.registration_number}</strong>).</p>
                        <p>After reviewing the inspection and documents, we regret to inform you that your vehicle could not be approved for listing at this time.</p>
                        <p><strong>Reason:</strong> {reason}</p>
                        <br/>
                        <p>Best regards,<br/>Auto Consultancy Team</p>
                    """,
                }
            ]
        }

    async def admin_vehicle_decision(
        self,
        vehicle_id: int,
        decision: VehicleDecisionRequest,
        admin_user: User,
    ) -> VehicleDecisionResponse:
        """
        Process admin decision (APPROVED or REJECTED) on a submitted vehicle.
        Validates inspection completion and mandatory documents before approval.
        Automatically creates a  Resale-Vehicle listing
        """
        if admin_user.role != "ADMIN":
            raise ForbiddenException(
                "Only Admins are authorized to approve or reject vehicles."
            )

        email_payload = None

        async with self.session.begin():
            vehicle = await self.vehicle_repository.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                raise NotFoundException("Vehicle not found.")

            if vehicle.status == "sold":
                raise BadRequestException(
                    "Cannot change decision for a vehicle that has already been sold."
                )

            if vehicle.status == "deactivated":
                raise BadRequestException(
                    "Cannot change decision for a deactivated vehicle."
                )

            if decision.action == "RESUBMIT":
                if vehicle.status != "rejected":
                    raise BadRequestException(
                        f"Cannot resubmit vehicle. Only rejected vehicles can be resubmitted (current status: '{vehicle.status}')."
                    )
                await self.vehicle_repository.update_vehicle_status(
                    vehicle_id, "submitted"
                )
                await self.vehicle_inspection_repository.reset_inspection_for_resubmission(
                    vehicle_id
                )
                return VehicleDecisionResponse(
                    vehicle_id=vehicle.id,
                    status="submitted",
                    message="Vehicle has been successfully resubmitted for inspection.",
                )

            inspection = (
                await self.vehicle_inspection_repository.get_inspection_by_vehicle_id(
                    vehicle_id
                )
            )
            if not inspection or inspection.status != "COMPLETED":
                raise BadRequestException(
                    "Cannot process decision. Vehicle inspection has not been completed."
                )

            if self.user_repository:
                seller = await self.user_repository.get_user_by_id(vehicle.seller_id)

            if decision.action == "APPROVED":
                # Check mandatory documents (RC, INSURANCE, PUC) using set to find the missing docs
                if self.vehicle_document_repository:
                    documents = await self.vehicle_document_repository.get_documents_by_vehicle_id(
                        vehicle_id
                    )
                    uploaded_types = {doc.document_type for doc in documents}
                    required_types = set(DOCUMENT_TYPES)
                    missing_docs = required_types - uploaded_types
                    if missing_docs:
                        raise BadRequestException(
                            f"Cannot approve vehicle. Missing required documents: {list(missing_docs)}."
                        )

                if (
                    not inspection.estimated_market_value
                    or inspection.estimated_market_value <= 0
                ):
                    raise BadRequestException(
                        "Inspection report is missing a valid estimated market value."
                    )

                # Update vehicle status to approved
                await self.vehicle_repository.update_vehicle_status(
                    vehicle_id, "approved"
                )

                listing_description = (
                    vehicle.description or "No description is mentioned"
                )

                # auto create listing if not exists
                listing = await self.vehicle_listing_repository.get_listing_by_vehicle_id(
                    vehicle.id
                )

                if not listing:
                    new_listing = (
                        await self.vehicle_listing_repository.create_listing(
                            vehicle_id=vehicle.id,
                            listed_price=inspection.estimated_market_value,
                            listing_description=listing_description,
                        )
                    )
                    listing_id = new_listing.id
                    listed_price = new_listing.listed_price
                else:
                    updated_listing = (
                        await self.vehicle_listing_repository.update_listing(
                            listing_id=listing.id,
                            status="ACTIVE",
                            listed_price=inspection.estimated_market_value,
                            description=listing_description,
                        )
                    )
                    listing_id = updated_listing.id
                    listed_price = updated_listing.listed_price

                if seller:
                    email_payload = self._approval_email_payload(
                        seller=seller,
                        vehicle=vehicle,
                        listed_price=inspection.estimated_market_value,
                    )

                response_data = VehicleDecisionResponse(
                    vehicle_id=vehicle.id,
                    status="approved",
                    message="Vehicle has been approved and listing created successfully.",
                    listing_id=listing_id,
                    listed_price=listed_price,
                )

            elif decision.action == "REJECTED":

                await self.vehicle_repository.update_vehicle_status(
                    vehicle_id, "rejected"
                )

                # soft-delete - deactivate existing listing if vehicle is moved to rejected

                await self.vehicle_listing_repository.deactivate_listing(vehicle.id)

                rejection_reason = (
                    decision.rejection_reason
                    or inspection.inspection_notes
                    or "No reason is mentioned"
                )

                if seller:
                    email_payload = self._rejection_email_payload(
                        seller=seller,
                        vehicle=vehicle,
                        reason=rejection_reason,
                    )

                response_data = VehicleDecisionResponse(
                    vehicle_id=vehicle.id,
                    status="rejected",
                    message="Vehicle submission has been rejected.",
                    listing_id=None,
                    listed_price=None,
                )

        # Sending notification email outside the DB transaction
        if self.email_service and email_payload:
            try:
                await self.email_service.send_mail(email_payload)
            except Exception:
                pass

        return response_data

    async def delete_vehicle(self, vehicle_id: int, user: User) -> dict:
        """
        Soft delete a vehicle.
        Seller can only delete when status is 'submitted' or 'rejected'.
        Admin can delete at any status except 'sold'.
        Cascades soft delete to vehicle listing if active.
        """
        async with self.session.begin():
            vehicle = await self.vehicle_repository.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                raise NotFoundException("Vehicle not found.")

            if vehicle.status == "deactivated":
                raise BadRequestException("Vehicle is already deactivated.")

            if vehicle.status == "sold":
                raise BadRequestException(
                    "Cannot delete a vehicle that has already been sold."
                )

            if user.role != "ADMIN":
                if vehicle.seller_id != user.id:
                    raise ForbiddenException(
                        "You do not have permission to delete this vehicle."
                    )

                if vehicle.status not in ("submitted", "rejected"):
                    raise BadRequestException(
                        f"Sellers cannot delete a vehicle in '{vehicle.status}' status. Only submitted or rejected vehicles can be deleted."
                    )

            await self.vehicle_repository.deactivate_vehicle(vehicle_id)

            await self.vehicle_listing_repository.deactivate_listing(vehicle_id)

            return {
                "vehicle_id": vehicle_id,
                "status": "deactivated",
                "message": "Vehicle deactivated successfully.",
            }
