import logging
from typing import Any
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_request_id
from app.schemas.response import ErrorResponse

logger = logging.getLogger("app.exceptions")


class AppException(Exception):
    """Base exception class for all custom application errors."""

    def __init__(self, message: str, status_code: int = 400, errors: Any = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(self.message)


class ValidationException(AppException):
    """Raised when business logic or payload validation fails (400 Bad Request)."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message=message, status_code=status_code)


class NotFoundException(AppException):
    """Raised when a requested resource is not found (404 Not Found)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class UnauthorizedException(AppException):
    """Raised when authentication is missing or invalid (401 Unauthorized)."""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    """Raised when user does not have required permissions (403 Forbidden)."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)


class ConflictException(AppException):
    """Raised when duplicate data or state conflict occurs (409 Conflict)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message=message, status_code=409)


class DatabaseException(AppException):
    """Exception raised for database operations errors (500 Internal Server Error)."""

    def __init__(
        self,
        message: str = "A database error occurred.",
        original_exception: Exception = None,
    ):
        self.original_exception = original_exception
        super().__init__(message=message, status_code=500)


# Register all global exceptions


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        response = ErrorResponse(
            success=False,
            status_code=429,
            message=f"Rate limit exceeded: {exc.detail}. Please try again later.",
            errors=None,
            request_id=get_request_id(),
        )
        return JSONResponse(
            status_code=429,
            content=response.model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        response = ErrorResponse(
            success=False,
            status_code=exc.status_code,
            message=exc.detail,
            errors=None,
            request_id=get_request_id(),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        formatted_errors = {}
        for error in exc.errors():
            field = str(error["loc"][-1]) if error["loc"] else "unknown"
            message = error["msg"]

            if field in formatted_errors:
                formatted_errors[field].append(message)
            else:
                formatted_errors[field] = [message]

        response = ErrorResponse(
            success=False,
            status_code=422,
            message="Validation Error",
            errors=formatted_errors,
            request_id=get_request_id(),
        )
        return JSONResponse(status_code=422, content=response.model_dump())

    @app.exception_handler(DatabaseException)
    async def database_exception_handler(request: Request, exc: DatabaseException):
        logger.error(f"Database error occurred: {exc.message}")
        response = ErrorResponse(
            success=False,
            status_code=500,
            message="A database error occurred.",
            errors=exc.message,
            request_id=get_request_id(),
        )
        return JSONResponse(status_code=500, content=response.model_dump())

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        response = ErrorResponse(
            success=False,
            status_code=exc.status_code,
            message=exc.message,
            errors=exc.errors,
            request_id=get_request_id(),
        )
        return JSONResponse(status_code=exc.status_code, content=response.model_dump())

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {str(exc)}")
        response = ErrorResponse(
            success=False,
            status_code=500,
            message="An unexpected error occurred.",
            errors=str(exc),
            request_id=get_request_id(),
        )
        return JSONResponse(status_code=500, content=response.model_dump())
