import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging import request_id_ctx

logger = logging.getLogger("api_access")


class TimeLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a Correlation / Request ID to every incoming request,
    tracks response processing duration, and records structured request logs.
    """

    def __init__(self, app, slow_threshold_sec: float = 0.5):
        super().__init__(app)
        self.slow_threshold_sec = slow_threshold_sec

    async def dispatch(self, request: Request, call_next):
        # 1. Extract existing X-Request-ID or generate a new UUID4
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # 2. Bind request_id to context variable and request state
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id

        start_time = time.time()

        try:
            # 3. Process the HTTP request
            response = await call_next(request)

            # 4. Calculate execution duration
            process_time = time.time() - start_time

            # 5. Inject X-Request-ID into outgoing response headers
            response.headers["X-Request-ID"] = request_id

            # 6. Structured logging with HTTP metadata
            client_ip = request.client.host if request.client else "unknown"
            logger.info(
                f"{request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.4f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "client_ip": client_ip,
                },
            )

            # 7. Warn if response exceeded slow threshold
            if process_time > self.slow_threshold_sec:
                logger.warning(
                    f"⚠️ SLOW API: {request.method} {request.url.path} took {process_time:.4f}s"
                )

            return response
        finally:
            # Clean up context variable
            request_id_ctx.reset(token)
