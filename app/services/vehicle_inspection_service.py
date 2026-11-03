from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle_inspection import VehicleInspection
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.schemas.vehicle_inspection import (
    ConsultantInspectionFilterParams,
    VehicleInspectionDetailSubmission,
)
from app.services.email_service import EmailService


class VehicleInspectionService:
    def __init__(
        self,
        session: AsyncSession,
        vehicle_inspection_repository: VehicleInspectionInterface,
        user_repository: UserInterface,
        email_service: EmailService,
    ):
        self.session = session
        self.vehicle_inspection_repository = vehicle_inspection_repository
        self.user_repository = user_repository
        self.email_service = email_service

    def _claim_success_payload(
        self, consultant: User, inspection_id: int, vehicle_id: int
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

    async def get_pending_inspections(self, page: int, limit: int) -> dict:
        async with self.session.begin():
            return await self.vehicle_inspection_repository.get_pending_unassigned_inspections(
                page=page, limit=limit
            )

    async def get_my_inspections(
        self, consultant: User, filters: ConsultantInspectionFilterParams
    ) -> dict:
        async with self.session.begin():
            data = await self.vehicle_inspection_repository.get_consultant_inspections(
                consultant_id=consultant.id,
                filters=filters,
            )
            data["consultant_id"] = consultant.id
            data["consultant_name"] = consultant.name
            return data

    async def claim_vehicle_inspection(
        self, inspection_id: int, consultant: User
    ) -> dict:

        async with self.session.begin():
            existing_inspection = (
                await self.vehicle_inspection_repository.get_inspection_by_id(
                    inspection_id
                )
            )

            if not existing_inspection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found",
                )

            if existing_inspection.consultant_id == consultant.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already claimed this inspection",
                )

            if existing_inspection.consultant_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inspection is already claimed by another consultant",
                )

            if existing_inspection.status != "PENDING":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inspection is not in pending status",
                )

            claimed_inspection = (
                await self.vehicle_inspection_repository.claim_inspection(
                    inspection_id=inspection_id, consultant_id=consultant.id
                )
            )

            if not claimed_inspection:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Failed to claim inspection. It may have just been claimed by another consultant.",
                )

            vehicle_id = claimed_inspection.vehicle_id

        payload = self._claim_success_payload(
            consultant=consultant,
            inspection_id=inspection_id,
            vehicle_id=vehicle_id,
        )
        await self.email_service.send_mail(payload)

        return {
            "consultant_id": consultant.id,
            "consultant_name": consultant.name,
            "vehicle_id": vehicle_id,
        }

    async def submit_inspection_report(
        self,
        inspection_id: int,
        consultant: User,
        report_data: VehicleInspectionDetailSubmission,
    ) -> VehicleInspection:
        async with self.session.begin():
            existing_inspection = (
                await self.vehicle_inspection_repository.get_inspection_by_id(
                    inspection_id
                )
            )

            if not existing_inspection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found",
                )

            if existing_inspection.consultant_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This inspection must be claimed before submitting a report",
                )

            if existing_inspection.consultant_id != consultant.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to submit a report for an inspection claimed by another consultant",
                )

            if existing_inspection.status == "COMPLETED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This inspection report has already been completed",
                )

            completed_inspection = (
                await self.vehicle_inspection_repository.submit_inspection_report(
                    inspection_id=inspection_id,
                    report_data=report_data,
                )
            )

            return completed_inspection
