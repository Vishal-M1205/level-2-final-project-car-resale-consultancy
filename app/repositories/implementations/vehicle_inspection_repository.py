import math

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vehicle import Vehicle
from app.models.vehicle_inspection import VehicleInspection
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.schemas.vehicle_inspection import (
    CustomerInspectionFilterParams,
    InspectionFilterParams,
    VehicleInspectionDetailSubmission,
)


class VehicleInspectionRepository(VehicleInspectionInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_inspections(
        self,
        filters: InspectionFilterParams | CustomerInspectionFilterParams,
        consultant_id: int | None = None,
        seller_id: int | None = None,
    ) -> dict:
        offset = (filters.page - 1) * filters.limit
        conditions = [Vehicle.status != "deactivated"]

        if filters.status:
            conditions.append(VehicleInspection.status == filters.status.upper())

        is_claimed = getattr(filters, "is_claimed", None)
        if is_claimed is True:
            conditions.append(VehicleInspection.consultant_id.is_not(None))
        elif is_claimed is False:
            conditions.append(VehicleInspection.consultant_id.is_(None))

        if consultant_id is not None:
            conditions.append(VehicleInspection.consultant_id == consultant_id)

        if seller_id is not None:
            conditions.append(Vehicle.seller_id == seller_id)

        vehicle_id = getattr(filters, "vehicle_id", None)
        if vehicle_id is not None:
            conditions.append(VehicleInspection.vehicle_id == vehicle_id)

        if filters.inspection_date:
            conditions.append(
                func.date(VehicleInspection.inspection_date) == filters.inspection_date
            )

        vehicle_status = getattr(filters, "vehicle_status", None)
        if vehicle_status:
            conditions.append(Vehicle.status == vehicle_status)

        stmnt = (
            select(VehicleInspection)
            .join(Vehicle, VehicleInspection.vehicle_id == Vehicle.id)
            .options(
                selectinload(VehicleInspection.vehicle),
                selectinload(VehicleInspection.consultant),
            )
            .where(and_(*conditions))
            .order_by(VehicleInspection.created_at.desc())
            .limit(filters.limit)
            .offset(offset)
        )
        rows = await self.session.execute(stmnt)
        inspections = list(rows.scalars().all())

        count_stmnt = (
            select(func.count())
            .select_from(VehicleInspection)
            .join(Vehicle, VehicleInspection.vehicle_id == Vehicle.id)
            .where(and_(*conditions))
        )
        row = await self.session.execute(count_stmnt)
        total_inspections = row.scalar_one() or 0

        total_pages = math.ceil(total_inspections / filters.limit) if total_inspections > 0 else 0

        return {
            "inspections": inspections,
            "page": filters.page,
            "limit": filters.limit,
            "total_pages": total_pages,
            "total_inspections": total_inspections,
        }

    async def create_pending_inspection(self, vehicle_id: int) -> VehicleInspection:
        stmnt = (
            insert(VehicleInspection)
            .values(vehicle_id=vehicle_id, status="PENDING", consultant_id=None)
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one()

    async def get_inspection_by_id(self, inspection_id: int) -> VehicleInspection | None:
        return await self.session.get(VehicleInspection, inspection_id)

    async def claim_inspection(
        self, inspection_id: int, consultant_id: int
    ) -> VehicleInspection | None:
        stmnt = (
            update(VehicleInspection)
            .where(
                VehicleInspection.id == inspection_id,
                VehicleInspection.consultant_id.is_(None),
                VehicleInspection.status == "PENDING",
            )
            # is_(None) is used to check whether other user already claimed
            .values(consultant_id=consultant_id)
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def unclaim_inspection(self, inspection_id: int) -> VehicleInspection | None:
        stmnt = (
            update(VehicleInspection)
            .where(
                VehicleInspection.id == inspection_id,
                VehicleInspection.consultant_id.is_not(None),
                VehicleInspection.status == "PENDING",
            )
            .values(consultant_id=None, updated_at=func.now())
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def cancel_inspection(self, inspection_id: int) -> VehicleInspection | None:
        stmnt = (
            update(VehicleInspection)
            .where(VehicleInspection.id == inspection_id)
            .values(status="CANCELLED", updated_at=func.now())
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def reset_inspection_for_resubmission(self, vehicle_id: int) -> VehicleInspection | None:
        stmnt = (
            update(VehicleInspection)
            .where(VehicleInspection.vehicle_id == vehicle_id)
            .values(
                status="PENDING",
                consultant_id=None,
                condition=None,
                engine_condition=None,
                exterior_condition=None,
                interior_condition=None,
                accident_history=None,
                estimated_market_value=None,
                inspection_notes=None,
                inspection_date=None,
                updated_at=func.now(),
            )
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def submit_inspection_report(
        self,
        inspection_id: int,
        report_data: VehicleInspectionDetailSubmission,
    ) -> VehicleInspection:

        stmnt = (
            update(VehicleInspection)
            .where(VehicleInspection.id == inspection_id)
            .values(
                **report_data.model_dump(),
                status="COMPLETED",
                inspection_date=func.now(),
            )
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        updated_inspection = result.scalar_one()

        # refresh vehicle relationship because VehicleInspectionDetailResponse has "vehicle" , where the
        # VehicleInspection has vehicle relationship
        await self.session.refresh(updated_inspection, ["vehicle"])
        return updated_inspection

    async def get_inspection_by_vehicle_id(self, vehicle_id: int) -> VehicleInspection | None:
        stmnt = (
            select(VehicleInspection)
            .where(VehicleInspection.vehicle_id == vehicle_id)
            .options(selectinload(VehicleInspection.vehicle))
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def get_inspection_with_details(self, inspection_id: int) -> VehicleInspection | None:
        stmnt = (
            select(VehicleInspection)
            .where(VehicleInspection.id == inspection_id)
            .options(
                selectinload(VehicleInspection.vehicle).selectinload(Vehicle.seller),
                selectinload(VehicleInspection.vehicle).selectinload(Vehicle.documents),
                selectinload(VehicleInspection.consultant),
            )
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def update_inspection_details(
        self,
        inspection_id: int,
        report_data: VehicleInspectionDetailSubmission,
    ) -> VehicleInspection:
        stmnt = (
            update(VehicleInspection)
            .where(VehicleInspection.id == inspection_id)
            .values(
                **report_data.model_dump(),
                updated_at=func.now(),
            )
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        updated_inspection = result.scalar_one()

        await self.session.refresh(updated_inspection, ["vehicle"])
        return updated_inspection
