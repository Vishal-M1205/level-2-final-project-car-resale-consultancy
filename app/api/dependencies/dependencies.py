from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.database.database import get_db_connection
from app.repositories.implementations.user_repository import UserRepository
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.implementations.vehicle_repository import VehicleRepository
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.repositories.implementations.vehicle_inspection_repository import (
    VehicleInspectionRepository,
)
from app.repositories.interfaces.vehicle_inspection_interface import (
    VehicleInspectionInterface,
)
from app.repositories.implementations.vehicle_document_repository import (
    VehicleDocumentRepository,
)
from app.repositories.interfaces.vehicle_document_interface import (
    VehicleDocumentInterface,
)
from app.repositories.implementations.vehicle_listing_repository import (
    VehicleListingRepository,
)
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.repositories.implementations.resale_transaction_repository import (
    ResaleTransactionRepository,
)
from app.repositories.interfaces.resale_transaction_interface import (
    ResaleTransactionInterface,
)
from app.exceptions import (
    ForbiddenException,
    SignatureError,
    TokenExpiredException,
    UnauthorizedException,
)
from app.schemas.auth import TokenData
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.vehicle_inspection_service import VehicleInspectionService
from app.services.vehicle_service import VehicleService
from app.services.vehicle_document_service import VehicleDocumentService
from app.services.vehicle_listing_service import VehicleListingService
from app.services.resale_transaction_service import ResaleTransactionService
from app.services.user_service import UserService
import jwt

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


def get_vehicle_repository(session: DB_Session) -> VehicleInterface:
    return VehicleRepository(session)


def get_vehicle_inspection_repository(
    session: DB_Session,
) -> VehicleInspectionInterface:
    return VehicleInspectionRepository(session)


def get_vehicle_listing_repository(
    session: DB_Session,
) -> VehicleListingInterface:
    return VehicleListingRepository(session)


def get_vehicle_document_repository(
    session: DB_Session,
) -> VehicleDocumentInterface:
    return VehicleDocumentRepository(session)


def get_resale_transaction_repository(
    session: DB_Session,
) -> ResaleTransactionInterface:
    return ResaleTransactionRepository(session)


def get_vehicle_service(
    session: DB_Session,
    vehicle_repository: Annotated[VehicleInterface, Depends(get_vehicle_repository)],
    vehicle_inspection_repository: Annotated[
        VehicleInspectionInterface, Depends(get_vehicle_inspection_repository)
    ],
    vehicle_document_repository: Annotated[
        VehicleDocumentInterface, Depends(get_vehicle_document_repository)
    ],
    vehicle_listing_repository: Annotated[
        VehicleListingInterface, Depends(get_vehicle_listing_repository)
    ],
    user_repository: Annotated[UserInterface, Depends(get_user_repository)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> VehicleService:
    return VehicleService(
        session,
        vehicle_repository,
        vehicle_inspection_repository,
        vehicle_document_repository,
        vehicle_listing_repository,
        user_repository,
        email_service,
    )


def get_vehicle_inspection_service(
    session: DB_Session,
    vehicle_inspection_repository: Annotated[
        VehicleInspectionInterface, Depends(get_vehicle_inspection_repository)
    ],
    vehicle_repository: Annotated[VehicleInterface, Depends(get_vehicle_repository)],
    user_repository: Annotated[UserInterface, Depends(get_user_repository)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
    vehicle_listing_repository: Annotated[
        VehicleListingInterface, Depends(get_vehicle_listing_repository)
    ],
) -> VehicleInspectionService:
    return VehicleInspectionService(
        session,
        vehicle_inspection_repository,
        vehicle_repository,
        user_repository,
        email_service,
        vehicle_listing_repository,
    )


def get_vehicle_document_service(
    session: DB_Session,
    vehicle_repository: Annotated[VehicleInterface, Depends(get_vehicle_repository)],
    vehicle_document_repository: Annotated[
        VehicleDocumentInterface, Depends(get_vehicle_document_repository)
    ],
) -> VehicleDocumentService:
    return VehicleDocumentService(
        session, vehicle_repository, vehicle_document_repository
    )


def get_vehicle_listing_service(
    session: DB_Session,
    vehicle_listing_repository: Annotated[
        VehicleListingInterface, Depends(get_vehicle_listing_repository)
    ],
    vehicle_repository: Annotated[VehicleInterface, Depends(get_vehicle_repository)],
) -> VehicleListingService:
    return VehicleListingService(
        session, vehicle_listing_repository, vehicle_repository
    )


def get_resale_transaction_service(
    session: DB_Session,
    resale_transaction_repository: Annotated[
        ResaleTransactionInterface, Depends(get_resale_transaction_repository)
    ],
    vehicle_listing_repository: Annotated[
        VehicleListingInterface, Depends(get_vehicle_listing_repository)
    ],
    vehicle_repository: Annotated[VehicleInterface, Depends(get_vehicle_repository)],
    user_repository: Annotated[UserInterface, Depends(get_user_repository)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> ResaleTransactionService:
    return ResaleTransactionService(
        session,
        resale_transaction_repository,
        vehicle_listing_repository,
        vehicle_repository,
        user_repository,
        email_service,
    )


def get_user_service(
    session: DB_Session,
    user_repository: Annotated[UserInterface, Depends(get_user_repository)],
    vehicle_listing_repository: Annotated[
        VehicleListingInterface, Depends(get_vehicle_listing_repository)
    ],
) -> UserService:
    return UserService(session, user_repository, vehicle_listing_repository)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    security_scopes: SecurityScopes,
    user_repository: Annotated[UserInterface, Depends(get_user_repository)],
    session: DB_Session,
):
    credentials_exception = UnauthorizedException("Could not validate credentials")
    try:
        payload = decode_access_token(token)

        if (
            payload.get("sub") is None
            or payload.get("role") is None
            or payload.get("type") != "access"
        ):
            raise credentials_exception

        token_data = TokenData(**payload)

        user = await user_repository.get_user_by_email(token_data.sub)

        await session.commit()

        if not user:
            raise credentials_exception

        for required_scopes in security_scopes.scopes:
            if required_scopes not in token_data.scopes:
                raise ForbiddenException("Not enough permission")

        return user

    except (
        SignatureError,
        TokenExpiredException,
        ForbiddenException,
        UnauthorizedException,
    ):
        raise
    except Exception:
        raise credentials_exception
