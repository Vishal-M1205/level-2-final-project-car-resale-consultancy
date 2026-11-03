from abc import ABC, abstractmethod

from app.models.vehicle_inspection import VehicleInspection
from app.schemas.vehicle_inspection import (
    ConsultantInspectionFilterParams,
    VehicleInspectionDetailSubmission,
)


class VehicleInspectionInterface(ABC):

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
    async def get_pending_unassigned_inspections(
        self, page: int, limit: int
    ) -> dict:
        pass

    @abstractmethod
    async def get_consultant_inspections(
        self, consultant_id: int, filters: ConsultantInspectionFilterParams
    ) -> dict:
        pass

    @abstractmethod
    async def submit_inspection_report(
        self,
        inspection_id: int,
        report_data: VehicleInspectionDetailSubmission,
    ) -> VehicleInspection:
        pass
