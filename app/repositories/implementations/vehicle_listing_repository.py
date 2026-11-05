import math
from decimal import Decimal

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vehicle import Vehicle
from app.models.vehicle_listing import VehicleListing
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.vehicle_listing import ListingFilterParams


class VehicleListingRepository(VehicleListingInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_listing(
        self,
        vehicle_id: int,
        listed_price: Decimal,
        listing_description: str | None,
        status: str = "ACTIVE",
    ) -> VehicleListing:
        stmnt = (
            insert(VehicleListing)
            .values(
                vehicle_id=vehicle_id,
                listed_price=listed_price,
                listing_description=listing_description,
                status=status,
            )
            .returning(VehicleListing)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one()

    async def get_listing_by_id(self, listing_id: int) -> VehicleListing | None:
        stmnt = (
            select(VehicleListing)
            .options(selectinload(VehicleListing.vehicle))
            .where(VehicleListing.id == listing_id)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def get_listings(self, filters: ListingFilterParams) -> dict:
        offset = (filters.page - 1) * filters.limit
        conditions = [Vehicle.status != "deactivated"]

        if filters.status:
            conditions.append(VehicleListing.status == filters.status)
        if filters.min_price is not None:
            conditions.append(VehicleListing.listed_price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(VehicleListing.listed_price <= filters.max_price)
        if filters.brand:
            conditions.append(Vehicle.brand.ilike(f"%{filters.brand}%"))

        stmnt = (
            select(VehicleListing)
            .join(Vehicle, VehicleListing.vehicle_id == Vehicle.id)
            .options(selectinload(VehicleListing.vehicle))
            .where(and_(*conditions))
            .order_by(VehicleListing.listed_at.desc())
            .limit(filters.limit)
            .offset(offset)
        )
        rows = await self.session.execute(stmnt)
        listings = list(rows.scalars().all())

        count_stmnt = (
            select(func.count())
            .select_from(VehicleListing)
            .join(Vehicle, VehicleListing.vehicle_id == Vehicle.id)
            .where(and_(*conditions))
        )
        total_listings = (await self.session.execute(count_stmnt)).scalar_one() or 0
        total_pages = math.ceil(total_listings / filters.limit) if total_listings > 0 else 0

        return {
            "listings": listings,
            "page": filters.page,
            "limit": filters.limit,
            "total_pages": total_pages,
            "total_listings": total_listings,
        }

    async def update_listing(
        self,
        listing_id: int,
        status: str | None = None,
        listed_price: Decimal | None = None,
        description: str | None = None,
    ) -> VehicleListing | None:
        values: dict = {"updated_at": func.now()}
        if status is not None:
            values["status"] = status
        if listed_price is not None:
            values["listed_price"] = listed_price
        if description is not None:
            values["listing_description"] = description

        stmnt = (
            update(VehicleListing)
            .where(VehicleListing.id == listing_id)
            .values(**values)
            .returning(VehicleListing)
        )
        result = await self.session.execute(stmnt)
        listing = result.scalar_one_or_none()
        if listing:
            await self.session.refresh(listing, ["vehicle"])
        return listing

    async def deactivate_listings_by_seller_id(self, seller_id: int) -> list[int]:
        find_stmnt = (
            select(VehicleListing.id)
            .join(Vehicle, VehicleListing.vehicle_id == Vehicle.id)
            .where(Vehicle.seller_id == seller_id, VehicleListing.status == "ACTIVE")
        )
        listing_ids = list((await self.session.execute(find_stmnt)).scalars().all())
        if listing_ids:
            update_stmnt = (
                update(VehicleListing)
                .where(VehicleListing.id.in_(listing_ids))
                .values(status="INACTIVE", updated_at=func.now())
            )
            await self.session.execute(update_stmnt)
        return listing_ids

    async def get_listing_by_vehicle_id(self, vehicle_id: int) -> VehicleListing | None:
        stmnt = select(VehicleListing).where(VehicleListing.vehicle_id == vehicle_id)
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def update_listing_description(
        self, vehicle_id: int, description: str | None
    ) -> VehicleListing | None:
        stmnt = (
            update(VehicleListing)
            .where(VehicleListing.vehicle_id == vehicle_id)
            .values(listing_description=description, updated_at=func.now())
            .returning(VehicleListing)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def update_listing_price(
        self, vehicle_id: int, listed_price: Decimal
    ) -> VehicleListing | None:
        stmnt = (
            update(VehicleListing)
            .where(VehicleListing.vehicle_id == vehicle_id)
            .values(listed_price=listed_price, updated_at=func.now())
            .returning(VehicleListing)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def deactivate_listing(self, vehicle_id: int) -> VehicleListing | None:
        stmnt = (
            update(VehicleListing)
            .where(VehicleListing.vehicle_id == vehicle_id)
            .values(status="INACTIVE", updated_at=func.now())
            .returning(VehicleListing)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def reactivate_listing(
        self,
        vehicle_id: int,
        listed_price: Decimal,
        listing_description: str | None,
    ) -> VehicleListing | None:
        stmnt = (
            update(VehicleListing)
            .where(VehicleListing.vehicle_id == vehicle_id)
            .values(
                status="ACTIVE",
                listed_price=listed_price,
                listing_description=listing_description,
                updated_at=func.now(),
            )
            .returning(VehicleListing)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()
