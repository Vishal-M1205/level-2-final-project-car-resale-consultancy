from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.user import UserFilterParams, UserPatchRequest


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
            raise ForbiddenException("Only administrators can list users.")

        async with self.session.begin():
            return await self.user_repository.get_users(
                page=filters.page,
                limit=filters.limit,
                role=filters.role,
                is_active=filters.is_active,
                search=filters.search,
                name=filters.name,
                email=filters.email,
                phone=filters.phone,
                district=filters.district,
                state=filters.state,
                gender=filters.gender,
                sort_by=filters.sort_by,
                order=filters.order,
            )

    async def get_my_profile(self, current_user: User) -> User:
        return await self.get_user_by_id(user_id=current_user.id, current_user=current_user)

    async def get_user_by_id(self, user_id: int, current_user: User) -> User:
        if current_user.role != "ADMIN" and current_user.id != user_id:
            raise ForbiddenException("You do not have permission to view other users' profiles.")

        async with self.session.begin():
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise NotFoundException("User not found.")
            return user

    async def soft_delete_user(self, user_id: int, current_user: User) -> dict:
        """
        Soft-deactivates a user account and cascades deactivation to their active marketplace listings.
        Guards: Admins cannot deactivate their own account; target user must be currently active.
        """
        if current_user.role != "ADMIN":
            raise ForbiddenException("Only administrators can deactivate users.")

        if current_user.id == user_id:
            raise BadRequestException("Administrators cannot deactivate their own account.")

        async with self.session.begin():
            target_user = await self.user_repository.get_user_by_id(user_id)
            if not target_user:
                raise NotFoundException("User not found.")

            if not target_user.is_active:
                raise BadRequestException("User is already deactivated.")

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

    async def patch_user(
        self, user_id: int, patch_data: UserPatchRequest, current_user: User
    ) -> User:
        if current_user.role != "ADMIN" and current_user.id != user_id:
            raise ForbiddenException("You can only update your own profile.")

        update_dict = patch_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise BadRequestException("No fields provided for update.")

        async with self.session.begin():
            existing_user = await self.user_repository.get_user_by_id(user_id)
            if not existing_user or not existing_user.is_active:
                raise NotFoundException("User not found or is inactive.")

            if "phone" in update_dict and update_dict["phone"] != existing_user.phone:
                phone_user = await self.user_repository.get_user_by_phone(update_dict["phone"])
                if phone_user and phone_user.id != user_id:
                    raise ConflictException("Phone number is already registered by another user.")

            updated_user = await self.user_repository.update_user(
                user_id=user_id, update_data=update_dict
            )
            return updated_user
