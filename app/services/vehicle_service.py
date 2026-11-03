from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.schemas.vehicle import VehicleFilterParams, VehicleSubmission


class VehicleService:
    def __init__(
        self,
        session: AsyncSession,
        vehicle_repository: VehicleInterface,
        vehicle_inspection_repository: VehicleInspectionInterface,
    ):
        self.session = session
        self.vehicle_repository = vehicle_repository
        self.vehicle_inspection_repository = vehicle_inspection_repository

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
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Vehicle with this registration number already found",
                )

            submitted_vehicle = await self.vehicle_repository.insert_vehicle_details(
                vehicle_details, seller_id
            )

            await self.vehicle_inspection_repository.create_pending_inspection(
                submitted_vehicle.id
            )

            return submitted_vehicle

    async def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle:
        async with self.session.begin():
            vehicle_details = await self.vehicle_repository.get_vehicle_by_id(
                vehicle_id
            )

            if not vehicle_details:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="No Vehicle found"
                )

            return vehicle_details

    async def get_user_vehicles(self, user: User, filters: VehicleFilterParams) -> dict:
        async with self.session.begin():
            data = await self.vehicle_repository.get_vehicles(
                filters=filters, seller_id=user.id
            )
            data["id"] = user.id
            data["name"] = user.name
            return data

    async def get_all_vehicles(self, filters: VehicleFilterParams) -> dict:
        async with self.session.begin():
            return await self.vehicle_repository.get_vehicles(filters=filters)
