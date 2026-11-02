from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.config import config
from app.api.routes.auth import router as auth_router
from app.scripts.create_admin import create_admin
from app.utilities.log import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_admin()
    yield


app = FastAPI(title="Car Resale Consultancy API", summary="", lifespan=lifespan)

app.include_router(auth_router)


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
