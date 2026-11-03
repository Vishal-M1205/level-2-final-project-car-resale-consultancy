from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import Token
from app.core.security import (
    hash_password,
    verify_hashed_password,
    create_access_token,
    create_refresh_token,
)
from app.models.user import User
from app.repositories.interfaces.user_interface import UserInterface
from app.schemas.auth import Login, RegisterUser
from app.services.email_service import EmailService


class AuthService:

    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserInterface,
        email_service: EmailService,
    ):
        self.session = session
        self.user_repository = user_repository
        self.email_service = email_service

    def _signup_mail_payload(recipient: str) -> dict:
        return {
            "Messages": [
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": recipient,
                        }
                    ],
                    "Subject": "Welcome to Car Resale Consultancy!",
                    "HTMLPart": """
                                <h1>Welcome Aboard!</h1>
                                <p>Your account has been successfully created.</p>
                                <p>Thank you for registering with Car Resale Consultancy.</p>
                                <p>We look forward to serving you!</p>
                            """,
                }
            ]
        }

    async def _register(self, user_data: RegisterUser, role: str) -> User:
        async with self.session.begin():
            existing_user = await self.user_repository.get_user_by_email(
                user_data.email
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already exists with this email",
                )

            existing_user = await self.user_repository.get_user_by_phone(
                user_data.phone
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already exists with this phone number",
                )

            hashed_password = hash_password(user_data.password)
            user = User(
                **user_data.model_dump(exclude={"password"}),
                hashed_password=hashed_password,
                role=role,
            )
            registered_user = await self.user_repository.register_user(user)
        payload = self._signup_mail_payload(user.email)
        await self.email_service.send_mail(payload)
        return registered_user

    async def register_user(self, user_data: RegisterUser) -> User:
        return await self._register(user_data, role="CUSTOMER")

    async def register_consultant(self, consultant_data: RegisterUser) -> User:
        return await self._register(consultant_data, role="CONSULTANT")

    async def login(self, login_credentials: Login):
        async with self.session.begin():
            user: User | None = await self.user_repository.get_user_by_email(
                login_credentials.email
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="No User found"
                )
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated",
                )

            hashed_password = user.hashed_password

            if not verify_hashed_password(hashed_password, login_credentials.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            access_token_payload = {"sub": user.email, "role": user.role}
            refresh_token_payload = {"sub": user.email}

            access_token = create_access_token(access_token_payload)
            refresh_token = create_refresh_token(refresh_token_payload)

            return Token(access_token=access_token, refresh_token=refresh_token)
