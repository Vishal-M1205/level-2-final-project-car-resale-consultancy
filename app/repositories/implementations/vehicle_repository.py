import math

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.schemas.vehicle import VehicleFilterParams, VehicleSubmission


class VehicleRepository(VehicleInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_vehicle_by_registration_number(
        self, registration_number: str
    ) -> Vehicle | None:
        stmnt = select(Vehicle).where(
            Vehicle.registration_number == registration_number
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def insert_vehicle_details(
        self, vehicle_details: VehicleSubmission, seller_id: int
    ) -> Vehicle:
        stmnt = (
            insert(Vehicle)
            .values(
                **vehicle_details.model_dump(), status="submitted", seller_id=seller_id
            )
            .returning(Vehicle)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one()

    async def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle | None:
        return await self.session.get(Vehicle, vehicle_id)

    async def get_vehicles(
        self, filters: VehicleFilterParams, seller_id: int | None = None
    ) -> dict:
        conditions = []

        # For getting specific user's vehicles
        if seller_id is not None:
            conditions.append(Vehicle.seller_id == seller_id)

        if filters.status:
            conditions.append(Vehicle.status == filters.status)
        else:
            conditions.append(Vehicle.status != "deactivated")
        if filters.fuel_type:
            conditions.append(Vehicle.fuel_type == filters.fuel_type)
        if filters.transmission:
            conditions.append(Vehicle.transmission == filters.transmission)

        if filters.brand:
            conditions.append(Vehicle.brand.ilike(f"%{filters.brand}%"))
        if filters.model:
            conditions.append(Vehicle.model.ilike(f"%{filters.model}%"))

        if filters.min_price is not None:
            conditions.append(Vehicle.expected_price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(Vehicle.expected_price <= filters.max_price)
        if filters.min_year is not None:
            conditions.append(Vehicle.manufacturing_year >= filters.min_year)
        if filters.max_year is not None:
            conditions.append(Vehicle.manufacturing_year <= filters.max_year)

        # Pagination
        offset = (filters.page - 1) * filters.limit
        stmnt = select(Vehicle).order_by(Vehicle.created_at.desc())

        if conditions:
            stmnt = stmnt.where(and_(*conditions))

        stmnt = stmnt.limit(filters.limit).offset(offset)
        rows = await self.session.execute(stmnt)
        vehicles = rows.scalars().all()

        count_stmnt = select(func.count()).select_from(Vehicle)
        if conditions:
            count_stmnt = count_stmnt.where(and_(*conditions))

        row = await self.session.execute(count_stmnt)
        total_vehicles = row.scalar_one() or 0

        total_pages = (
            math.ceil(total_vehicles / filters.limit) if total_vehicles > 0 else 0
        )

        return {
            "vehicles": vehicles,
            "page": filters.page,
            "limit": filters.limit,
            "total_pages": total_pages,
            "total_vehicles": total_vehicles,
        }

    async def update_vehicle_status(
        self, vehicle_id: int, status: str
    ) -> Vehicle | None:
        stmnt = (
            update(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .values(status=status, updated_at=func.now())
            .returning(Vehicle)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def update_vehicle_details(
        self, vehicle_id: int, update_data: dict
    ) -> Vehicle | None:
        stmnt = (
            update(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .values(**update_data, updated_at=func.now())
            .returning(Vehicle)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def deactivate_vehicle(self, vehicle_id: int) -> Vehicle | None:
        stmnt = (
            update(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .values(status="deactivated", updated_at=func.now())
            .returning(Vehicle)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()
