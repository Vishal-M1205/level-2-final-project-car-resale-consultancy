from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.database.database import get_db_connection
from app.repositories.implementations.user_repository import UserRepository
from app.repositories.interfaces.user_interface import UserInterface
from app.schemas.auth import TokenData
from app.services.auth_service import AuthService
import jwt

from app.services.email_service import EmailService

DB_Session = Annotated[AsyncSession, Depends(get_db_connection)]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_email_service(request: Request):
    return EmailService(request.app.state.client)


def get_user_repository(session: DB_Session) -> UserInterface:
    return UserRepository(session)


def get_auth_service(
    session: DB_Session,
    user_repository: Annotated[UserInterface, Depends(get_user_repository)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> AuthService:
    return AuthService(session, user_repository, email_service)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    security_scopes: SecurityScopes,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    session: DB_Session,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = decode_token(token)

        if (
            payload["sub"] is None
            or payload["role"] is None
            or payload["type"] != "access"
        ):
            raise credentials_exception

        token_data = TokenData(**payload)

        user = await user_repository.get_user_by_email(token_data.sub)

        await session.commit()

        if not user:
            raise credentials_exception

        for required_scopes in security_scopes.scopes:
            if required_scopes not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permission",
                )

        return user

    except (jwt.PyJWTError, Exception):
        raise
