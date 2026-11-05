import math
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resale_transaction import ResaleTransaction
from app.models.vehicle_listing import VehicleListing
from app.repositories.interfaces.resale_transaction_interface import (
    ResaleTransactionInterface,
)
from app.schemas.resale_transaction import TransactionFilterParams


class ResaleTransactionRepository(ResaleTransactionInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_transaction(
        self,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
        final_price: Decimal,
        consultant_id: int | None = None,
        delivery_date: datetime | None = None,
        delivery_notes: str | None = None,
    ) -> ResaleTransaction:
        if delivery_date is not None and delivery_date.tzinfo is not None:
            delivery_date = delivery_date.astimezone(timezone.utc).replace(tzinfo=None)

        stmnt = (
            insert(ResaleTransaction)
            .values(
                listing_id=listing_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                consultant_id=consultant_id,
                final_price=final_price,
                status="CONFIRMED",
                delivery_date=delivery_date,
                delivery_notes=delivery_notes,
            )
            .returning(ResaleTransaction)
        )
        result = await self.session.execute(stmnt)
        transaction = result.scalar_one()

        await self.session.refresh(
            transaction,
            ["buyer", "seller", "consultant", "listing"],
        )
        if transaction.listing:
            await self.session.refresh(transaction.listing, ["vehicle"])

        return transaction

    async def get_transactions(
        self,
        filters: TransactionFilterParams,
        user_id: int | None = None,
        role: str | None = None,
    ) -> dict:
        offset = (filters.page - 1) * filters.limit
        conditions = []

        if filters.status:
            conditions.append(ResaleTransaction.status == filters.status.upper())

        if role == "CUSTOMER" and user_id is not None:
            conditions.append(
                or_(
                    ResaleTransaction.buyer_id == user_id,
                    ResaleTransaction.seller_id == user_id,
                )
            )
        elif role == "CONSULTANT" and user_id is not None:
            conditions.append(ResaleTransaction.consultant_id == user_id)

        where_clause = and_(*conditions) if conditions else True

        stmnt = (
            select(ResaleTransaction)
            .options(
                selectinload(ResaleTransaction.buyer),
                selectinload(ResaleTransaction.seller),
                selectinload(ResaleTransaction.consultant),
                selectinload(ResaleTransaction.listing).selectinload(VehicleListing.vehicle),
            )
            .where(where_clause)
            .order_by(ResaleTransaction.created_at.desc())
            .limit(filters.limit)
            .offset(offset)
        )
        rows = await self.session.execute(stmnt)
        transactions = list(rows.scalars().all())

        count_stmnt = select(func.count()).select_from(ResaleTransaction).where(where_clause)
        total_transactions = (await self.session.execute(count_stmnt)).scalar_one() or 0
        total_pages = math.ceil(total_transactions / filters.limit) if total_transactions > 0 else 0

        return {
            "transactions": transactions,
            "page": filters.page,
            "limit": filters.limit,
            "total_pages": total_pages,
            "total_transactions": total_transactions,
        }

    async def get_transaction_by_id(self, transaction_id: int) -> ResaleTransaction | None:
        stmnt = (
            select(ResaleTransaction)
            .options(
                selectinload(ResaleTransaction.buyer),
                selectinload(ResaleTransaction.seller),
                selectinload(ResaleTransaction.consultant),
                selectinload(ResaleTransaction.listing).selectinload(VehicleListing.vehicle),
            )
            .where(ResaleTransaction.id == transaction_id)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def update_transaction(
        self, transaction_id: int, update_data: dict
    ) -> ResaleTransaction | None:
        if "delivery_date" in update_data and update_data["delivery_date"] is not None:
            val = update_data["delivery_date"]
            if getattr(val, "tzinfo", None) is not None:
                update_data["delivery_date"] = val.astimezone(timezone.utc).replace(tzinfo=None)

        update_data["updated_at"] = func.now()
        stmnt = (
            update(ResaleTransaction)
            .where(ResaleTransaction.id == transaction_id)
            .values(**update_data)
            .returning(ResaleTransaction)
        )
        result = await self.session.execute(stmnt)
        tx = result.scalar_one_or_none()
        if tx:
            await self.session.refresh(tx, ["buyer", "seller", "consultant", "listing"])
            if tx.listing:
                await self.session.refresh(tx.listing, ["vehicle"])
        return tx
