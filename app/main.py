from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import httpx
from app.core.config import config
from app.api.routes.auth import router as auth_router
from app.api.routes.vehicle import router as vehicle_router
from app.api.routes.vehicle_inspection import router as vehicle_inspection_router
from app.exceptions.email_exception import EmailException
from app.scripts.create_admin import create_admin
from app.utilities.log import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_admin()
    timeout = httpx.Timeout(connect=5, pool=5, read=10, write=10)
    limits = httpx.Limits(
        max_connections=10, max_keepalive_connections=5, keepalive_expiry=30
    )
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


app = FastAPI(title="Car Resale Consultancy API", summary="", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(vehicle_router)
app.include_router(vehicle_inspection_router)


@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["Health Checkup"])
def get_api_health():
    return JSONResponse({"health": "OK", "server": "running"})


@app.get("/", status_code=status.HTTP_200_OK, tags=["Root Path"])
def root_path():
    return JSONResponse(
        {"API-Name": config.api_name, "API-Version": config.api_version}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error processing %s %s: %s", request.method, request.url.path, exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


@app.exception_handler(EmailException)
async def email_exception_handler(request: Request, exc: EmailException):
    logger.exception(
        "Email Service Error %s %s: %s", request.method, request.url.path, exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Email Service Error"},
    )
