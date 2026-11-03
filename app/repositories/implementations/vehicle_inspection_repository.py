import math
from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vehicle_inspection import VehicleInspection
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.schemas.vehicle_inspection import (
    ConsultantInspectionFilterParams,
    VehicleInspectionDetailSubmission,
)


class VehicleInspectionRepository(VehicleInspectionInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_pending_inspection(self, vehicle_id: int) -> VehicleInspection:
        stmnt = (
            insert(VehicleInspection)
            .values(vehicle_id=vehicle_id, status="PENDING", consultant_id=None)
            .returning(VehicleInspection)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one()

    async def get_inspection_by_id(
        self, inspection_id: int
    ) -> VehicleInspection | None:
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

    async def get_pending_unassigned_inspections(self, page: int, limit: int) -> dict:
        offset = (page - 1) * limit

        # Vehicle is associated with VehicleInspection through a one to one relationship
        stmnt = (
            select(VehicleInspection)
            .options(selectinload(VehicleInspection.vehicle))
            .where(
                VehicleInspection.status == "PENDING",
                VehicleInspection.consultant_id.is_(None),
            )
            .order_by(VehicleInspection.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = await self.session.execute(stmnt)
        inspections = rows.scalars().all()

        count_stmnt = (
            select(func.count())
            .select_from(VehicleInspection)
            .where(
                VehicleInspection.status == "PENDING",
                VehicleInspection.consultant_id.is_(None),
            )
        )
        row = await self.session.execute(count_stmnt)
        total_inspections = row.scalar_one() or 0

        total_pages = (
            math.ceil(total_inspections / limit) if total_inspections > 0 else 0
        )

        return {
            "inspections": inspections,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_inspections": total_inspections,
        }

    async def get_consultant_inspections(
        self, consultant_id: int, filters: ConsultantInspectionFilterParams
    ) -> dict:
        offset = (filters.page - 1) * filters.limit
        conditions = [VehicleInspection.consultant_id == consultant_id]

        if filters.status:
            conditions.append(VehicleInspection.status == filters.status.upper())
        if filters.inspection_date:
            conditions.append(
                func.date(VehicleInspection.inspection_date) == filters.inspection_date
            )

        stmnt = (
            select(VehicleInspection)
            .options(selectinload(VehicleInspection.vehicle))
            .where(and_(*conditions))
            .order_by(VehicleInspection.created_at.desc())
            .limit(filters.limit)
            .offset(offset)
        )
        rows = await self.session.execute(stmnt)
        inspections = rows.scalars().all()

        count_stmnt = (
            select(func.count()).select_from(VehicleInspection).where(and_(*conditions))
        )
        row = await self.session.execute(count_stmnt)
        total_inspections = row.scalar_one() or 0

        total_pages = (
            math.ceil(total_inspections / filters.limit) if total_inspections > 0 else 0
        )

        return {
            "inspections": inspections,
            "page": filters.page,
            "limit": filters.limit,
            "total_pages": total_pages,
            "total_inspections": total_inspections,
        }

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
