from typing import Annotated

from fastapi import APIRouter, Security, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.dependencies import get_auth_service, get_current_user
from app.schemas.auth import (
    Login,
    RefreshTokenRequest,
    RegisterResponse,
    RegisterUser,
    Token,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register/user",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    service: Annotated[AuthService, Depends(get_auth_service)], user_data: RegisterUser
):
    """Register a new customer user, service available to public"""
    return await service.register_user(user_data)


@router.post(
    "/register/consultant",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_consultant(
    service: Annotated[AuthService, Depends(get_auth_service)],
    consultant_data: RegisterUser,
    current_user=Security(get_current_user, scopes=["user:create"]),
):
    """Register a new consultant"""
    return await service.register_consultant(consultant_data)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    service: Annotated[AuthService, Depends(get_auth_service)],
    login_credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Login the user,consultant and admin returns the JWT Token"""
    return await service.login(
        Login(email=login_credentials.username, password=login_credentials.password)
    )


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Generate a new access token using a valid refresh token."""
    return await service.refresh_access_token(refresh_request.refresh_token)
