import logging

from app.core.security import hash_password
from app.database.database import AsyncSessionMaker
from app.models.user import User
from app.repositories.implementations.user_repository import UserRepository

logger = logging.getLogger(__name__)

ADMIN_NAME = "System Admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPassword@123"
ADMIN_PHONE = "9999999999"


async def create_admin():
    async with AsyncSessionMaker() as session:
        user_repository = UserRepository(session)
        existing_user = await user_repository.get_user_by_email(ADMIN_EMAIL)
        if existing_user:
            logger.info(f"Admin already exists with email: {ADMIN_EMAIL}")
            return existing_user
        else:
            admin = User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                phone=ADMIN_PHONE,
                role="ADMIN",
                is_active=True,
                age=30,
                gender="MALE",
                address_line_1="Headquarters",
                district="Coimbatore",
                state="Tamil Nadu",
                pincode="641001",
            )

            created_admin = await user_repository.register_user(admin)
            await session.commit()

            logger.info(f"Admin with email : {ADMIN_EMAIL} created successfully")
            return created_admin
