from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.user import UserFilterParams


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserInterface,
        vehicle_listing_repository: VehicleListingInterface,
    ):
        self.session = session
        self.user_repository = user_repository
        self.vehicle_listing_repository = vehicle_listing_repository

    async def get_users(self, filters: UserFilterParams, current_user: User) -> dict:
        if current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can list users.",
            )

        async with self.session.begin():
            return await self.user_repository.get_users(
                page=filters.page,
                limit=filters.limit,
                role=filters.role,
                is_active=filters.is_active,
            )

    async def get_user_by_id(self, user_id: int, current_user: User) -> User:
        if current_user.role != "ADMIN" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view other users' profiles.",
            )

        async with self.session.begin():
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )
            return user

    async def soft_delete_user(self, user_id: int, current_user: User) -> dict:
        if current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can deactivate users.",
            )

        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot deactivate their own account.",
            )

        async with self.session.begin():
            target_user = await self.user_repository.get_user_by_id(user_id)
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            if not target_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already deactivated.",
                )

            # Soft delete user
            await self.user_repository.soft_delete_user(user_id)

            # Cascade: deactivate active listings owned by this user
            deactivated_listing_ids = (
                await self.vehicle_listing_repository.deactivate_listings_by_seller_id(
                    seller_id=user_id
                )
            )

            return {
                "user_id": user_id,
                "is_active": False,
                "message": f"User #{user_id} successfully deactivated and {len(deactivated_listing_ids)} active listings set to INACTIVE.",
                "deactivated_listings_count": len(deactivated_listing_ids),
            }

