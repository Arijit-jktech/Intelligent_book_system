"""
Request/Response Middleware
Logging and monitoring for all HTTP requests and responses.
"""

import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.structured_logging import (
    get_logger,
    set_request_id,
    set_user_id,
    get_request_id
)

logger = get_logger(__name__)


class RequestResponseMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with correlation IDs."""
    
    # Endpoints to skip logging (avoid noise)
    SKIP_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with logging.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
        
        Returns:
            HTTP response with tracking headers
        """
        # Get or create request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)
        
        # Try to extract user ID from token (if authenticated)
        try:
            # This is a simple check; actual extraction depends on your auth scheme
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # In production, you'd decode the JWT here
                # For now, just mark that we have a bearer token
                set_user_id("authenticated")
        except Exception:
            pass
        
        # Skip logging for certain paths
        if request.url.path in self.SKIP_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Capture request info
        start_time = time.time()
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info_with_context(
            f"Request started: {method} {path}",
            request_id=request_id,
            method=method,
            path=path,
            client_host=client_host,
            query_string=str(request.url.query) if request.url.query else None
        )
        
        try:
            # Call the endpoint
            response = await call_next(request)
        except Exception as exc:
            # Log exception and re-raise
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error_with_context(
                f"Request failed: {method} {path}",
                request_id=request_id,
                method=method,
                path=path,
                duration_ms=duration_ms,
                error=str(exc)[:200],
                exc_info=exc
            )
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)
        status_code = response.status_code
        
        # Log response
        log_level = "error" if status_code >= 500 else "warning" if status_code >= 400 else "info"
        
        logger.info_with_context(
            f"Request completed: {method} {path} {status_code}",
            request_id=request_id,
            method=method,
            path=path,
            status=status_code,
            duration_ms=duration_ms,
            client_host=client_host
        )
        
        # Add tracking headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(duration)
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle errors consistently.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
        
        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            request_id = get_request_id()
            logger.error_with_context(
                f"Unhandled exception: {exc.__class__.__name__}",
                request_id=request_id,
                error=str(exc)[:200],
                exc_info=exc
            )
            raise


__all__ = [
    'RequestResponseMiddleware',
    'ErrorHandlingMiddleware',
]
