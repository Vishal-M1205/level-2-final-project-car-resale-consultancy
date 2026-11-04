from abc import ABC, abstractmethod

from app.models.vehicle_inspection import VehicleInspection
from app.schemas.vehicle_inspection import (
    InspectionFilterParams,
    VehicleInspectionDetailSubmission,
)


class VehicleInspectionInterface(ABC):

    @abstractmethod
    async def get_inspections(
        self, filters: InspectionFilterParams, consultant_id: int | None = None
    ) -> dict:
        pass

    @abstractmethod
    async def create_pending_inspection(self, vehicle_id: int) -> VehicleInspection:
        pass

    @abstractmethod
    async def get_inspection_by_id(
        self, inspection_id: int
    ) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def claim_inspection(
        self, inspection_id: int, consultant_id: int
    ) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def unclaim_inspection(self, inspection_id: int) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def cancel_inspection(self, inspection_id: int) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def reset_inspection_for_resubmission(
        self, vehicle_id: int
    ) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def submit_inspection_report(
        self,
        inspection_id: int,
        report_data: VehicleInspectionDetailSubmission,
    ) -> VehicleInspection:
        pass

    @abstractmethod
    async def get_inspection_by_vehicle_id(
        self, vehicle_id: int
    ) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def get_inspection_with_details(
        self, inspection_id: int
    ) -> VehicleInspection | None:
        pass

    @abstractmethod
    async def update_inspection_details(
        self,
        inspection_id: int,
        report_data: VehicleInspectionDetailSubmission,
    ) -> VehicleInspection:
        pass
