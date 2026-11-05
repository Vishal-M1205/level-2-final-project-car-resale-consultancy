import base64
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware that:
    1. Generates or propagates an 'X-Correlation-ID' header for request tracing.
    2. Measures request execution duration using time.perf_counter().
    3. Sets an HTTP-only cookie containing essential request context details.
    4. Logs the incoming request, status code, and time taken using the configured logger.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Correlation ID: Extract from incoming headers or generate a new UUID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # 2. Timing: Start high-precision performance counter
        start_time = time.perf_counter()
        request_time = datetime.now(timezone.utc).isoformat()

        client_host = request.client.host if request.client else "unknown"

        # 3. Log incoming request
        logger.info(
            f"Incoming Request: {request.method} {request.url.path} from {client_host} | Correlation-ID: {correlation_id}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request Failed: {request.method} {request.url.path} in {elapsed_time_ms:.2f}ms | "
                f"Correlation-ID: {correlation_id} | Error: {exc}"
            )
            raise exc

        # Calculate total duration in milliseconds
        elapsed_time_ms = (time.perf_counter() - start_time) * 1000

        # Attach Correlation-ID and Processing Time headers to the response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{elapsed_time_ms:.2f}ms"

        # 4. Send cookie containing essential tracking details (Base64 encoded JSON)
        cookie_details = {
            "correlation_id": correlation_id,
            "timestamp": request_time,
            "path": request.url.path,
        }
        encoded_cookie_value = base64.b64encode(json.dumps(cookie_details).encode("utf-8")).decode(
            "utf-8"
        )

        response.set_cookie(
            key="request_context",
            value=encoded_cookie_value,
            httponly=True,
            samesite="lax",
            max_age=3600,  # 1 hour
        )

        # Also set a simple correlation_id cookie for direct access
        response.set_cookie(
            key="correlation_id",
            value=correlation_id,
            httponly=True,
            samesite="lax",
            max_age=3600,
        )

        # 5. Log completed request with execution time
        logger.info(
            f"Completed Request: {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time Taken: {elapsed_time_ms:.2f}ms | "
            f"Correlation-ID: {correlation_id}"
        )

        return response
