from abc import ABC, abstractmethod

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleFilterParams, VehicleSubmission


class VehicleInterface(ABC):

    @abstractmethod
    async def get_vehicle_by_registration_number(
        self, registration_number: str
    ) -> Vehicle | None:
        pass

    @abstractmethod
    async def insert_vehicle_details(
        self, vehicle_details: VehicleSubmission, seller_id: int
    ) -> Vehicle:
        pass

    @abstractmethod
    async def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle | None:
        pass

    @abstractmethod
    async def get_vehicles(
        self, filters: VehicleFilterParams, seller_id: int | None = None
    ) -> dict:
        pass
