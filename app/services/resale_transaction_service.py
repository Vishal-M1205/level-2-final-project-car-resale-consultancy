from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resale_transaction import ResaleTransaction
from app.models.user import User
from app.repositories.interfaces.resale_transaction_interface import (
    ResaleTransactionInterface,
)
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.resale_transaction import (
    CreateResaleTransactionRequest,
    TransactionFilterParams,
)


class ResaleTransactionService:
    def __init__(
        self,
        session: AsyncSession,
        resale_transaction_repository: ResaleTransactionInterface,
        vehicle_listing_repository: VehicleListingInterface,
        vehicle_repository: VehicleInterface,
        user_repository: UserInterface,
    ):
        self.session = session
        self.resale_transaction_repository = resale_transaction_repository
        self.vehicle_listing_repository = vehicle_listing_repository
        self.vehicle_repository = vehicle_repository
        self.user_repository = user_repository

    async def log_resale_transaction(
        self, request: CreateResaleTransactionRequest, user: User
    ) -> ResaleTransaction:
        if user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can record resale transactions.",
            )

        async with self.session.begin():
            listing = await self.vehicle_listing_repository.get_listing_by_id(
                request.listing_id
            )
            if not listing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vehicle listing not found.",
                )

            if listing.status != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot record sale for listing in '{listing.status}' status. Only ACTIVE listings can be sold.",
                )

            vehicle = await self.vehicle_repository.get_vehicle_by_id(
                listing.vehicle_id
            )
            if not vehicle or vehicle.status == "deactivated":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Associated vehicle is not valid or has been deactivated.",
                )

            buyer = await self.user_repository.get_user_by_id(request.buyer_id)
            if not buyer or not buyer.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Buyer not found or is inactive.",
                )

            if request.buyer_id == vehicle.seller_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The vehicle seller cannot be the buyer in a resale transaction.",
                )

            if request.consultant_id is not None:
                consultant = await self.user_repository.get_user_by_id(
                    request.consultant_id
                )
                if not consultant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Consultant not found.",
                    )

            # Record transaction
            transaction = (
                await self.resale_transaction_repository.create_transaction(
                    listing_id=listing.id,
                    buyer_id=request.buyer_id,
                    seller_id=vehicle.seller_id,
                    final_price=request.final_price,
                    consultant_id=request.consultant_id,
                    delivery_date=request.delivery_date,
                    delivery_notes=request.delivery_notes,
                )
            )

            # Mark listing as SOLD
            await self.vehicle_listing_repository.update_listing(
                listing_id=listing.id,
                status="SOLD",
            )

            # Mark vehicle as sold
            await self.vehicle_repository.update_vehicle_status(
                vehicle_id=vehicle.id,
                status="sold",
            )

            return transaction

    async def get_transactions(
        self, filters: TransactionFilterParams, user: User
    ) -> dict:
        async with self.session.begin():
            return await self.resale_transaction_repository.get_transactions(
                filters=filters,
                user_id=user.id,
                role=user.role,
            )

