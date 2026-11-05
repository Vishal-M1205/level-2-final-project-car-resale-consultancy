import logging
from contextlib import asynccontextmanager

import httpx
import jwt
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.resale_transaction import router as resale_transaction_router
from app.api.routes.user import router as user_router
from app.api.routes.vehicle import router as vehicle_router
from app.api.routes.vehicle_inspection import router as vehicle_inspection_router
from app.api.routes.vehicle_listing import router as vehicle_listing_router
from app.core.config import config
from app.exceptions import AppException, EmailException
from app.middleware import RequestLoggingMiddleware
from app.scripts.create_admin import create_admin
from app.utilities.log import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_admin()
    timeout = httpx.Timeout(connect=5, pool=5, read=10, write=10)
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5, keepalive_expiry=30)
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        headers=headers,
        auth=(config.mailjet_api_key, config.mailjet_secret_key),
    ) as client:
        app.state.client = client
        yield


app = FastAPI(
    title="Car Resale Consultancy API",
    summary="Comprehensive REST API for Car Resale Consultancy platform.",
    description=(
        "FastAPI-based platform managing vehicle inspection workflows, listings, "
        "resale transactions, and user management with role-based access control."
    ),
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(vehicle_router)
app.include_router(vehicle_inspection_router)
app.include_router(vehicle_listing_router)
app.include_router(resale_transaction_router)


@app.get(
    "/api/health",
    status_code=status.HTTP_200_OK,
    tags=["Health Checkup"],
    summary="Service health check",
    description="Health check endpoint verifying that the API server is online and operational.",
)
def get_api_health():
    return JSONResponse({"health": "OK", "server": "running"})


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["Root Path"],
    summary="Root API information",
    description="Returns the platform service name and active API version.",
)
def root_path():
    return JSONResponse({"API-Name": config.api_name, "API-Version": config.api_version})


# =====================================================================
# GLOBAL EXCEPTION HANDLERS
# =====================================================================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        "Application exception processing %s %s: [%s] %s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    headers = None
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        headers = {"WWW-Authenticate": "Bearer"}
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(jwt.InvalidSignatureError)
async def jwt_invalid_signature_handler(request: Request, exc: jwt.InvalidSignatureError):
    logger.warning(
        "JWT signature verification failed on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token signature"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(jwt.ExpiredSignatureError)
async def jwt_expired_signature_handler(request: Request, exc: jwt.ExpiredSignatureError):
    logger.warning(
        "JWT signature expired on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token has expired"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(jwt.PyJWTError)
async def pyjwt_error_handler(request: Request, exc: jwt.PyJWTError):
    logger.warning(
        "PyJWT error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(EmailException)
async def email_exception_handler(request: Request, exc: EmailException):
    logger.exception("Email Service Error %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Email Service Error"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
