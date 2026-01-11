"""
Exception Handlers
Centralized exception handling for consistent error responses with correlation IDs.
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DBAPIError
from pydantic import ValidationError

from app.core.structured_logging import get_logger, get_request_id

logger = get_logger(__name__)


class ApplicationError(Exception):
    """Base application error."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationErrorResponse(Exception):
    """Validation error with details."""
    def __init__(self, details: str, status_code: int = 422):
        self.details = details
        self.status_code = status_code
        super().__init__(self.details)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError):
        """Handle application errors."""
        request_id = get_request_id()
        logger.error_with_context(
            f"Application error: {exc.message}",
            status_code=exc.status_code,
            request_id=request_id
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_type": "application_error",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity errors (duplicate keys, etc)."""
        request_id = get_request_id()
        logger.error_with_context(
            "Database integrity error",
            error_type="IntegrityError",
            request_id=request_id,
            details=str(exc.orig) if exc.orig else str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Record already exists or violates unique constraint",
                "error_type": "integrity_error",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """Handle generic SQLAlchemy errors."""
        request_id = get_request_id()
        error_type = exc.__class__.__name__
        
        logger.error_with_context(
            "Database error",
            error_type=error_type,
            request_id=request_id,
            details=str(exc)[:200]  # Limit detail length
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Database operation failed",
                "error_type": "database_error",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        request_id = get_request_id()
        
        # Extract field errors
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"][1:]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning_with_context(
            "Validation error",
            request_id=request_id,
            error_count=len(errors)
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation failed",
                "errors": errors,
                "request_id": request_id
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle value errors."""
        request_id = get_request_id()
        logger.warning_with_context(
            f"Value error: {str(exc)}",
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "error_type": "value_error",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        request_id = get_request_id()
        error_type = exc.__class__.__name__
        
        logger.error_with_context(
            f"Unexpected error: {error_type}",
            request_id=request_id,
            error_message=str(exc)[:200],
            exc_info=exc
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred",
                "error_type": error_type,
                "request_id": request_id
            }
        )


__all__ = [
    'ApplicationError',
    'ValidationErrorResponse',
    'register_exception_handlers',
]
