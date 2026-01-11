"""
Structured Logging Configuration
Provides JSON-formatted structured logging with request correlation IDs.
"""

import json
import logging
import uuid
import time
from contextvars import ContextVar
from datetime import datetime
from typing import Optional, Dict, Any

# Context variable for request correlation
request_id_context: ContextVar[str] = ContextVar('request_id', default='unknown')
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging compatible with log aggregators."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
            "user_id": user_id_context.get(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Include exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj, default=str)


class StructuredLogger(logging.LoggerAdapter):
    """Enhanced logger with structured logging support."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add extra fields."""
        return msg, kwargs
    
    def log_with_context(
        self, 
        level: int, 
        msg: str, 
        extra_fields: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log with additional context fields."""
        record_attrs = {"extra_fields": extra_fields or {}}
        self.log(level, msg, extra=record_attrs, **kwargs)
    
    def debug_with_context(self, msg: str, **context):
        """Debug log with context."""
        self.log_with_context(logging.DEBUG, msg, context)
    
    def info_with_context(self, msg: str, **context):
        """Info log with context."""
        self.log_with_context(logging.INFO, msg, context)
    
    def warning_with_context(self, msg: str, **context):
        """Warning log with context."""
        self.log_with_context(logging.WARNING, msg, context)
    
    def error_with_context(self, msg: str, **context):
        """Error log with context."""
        self.log_with_context(logging.ERROR, msg, context)
    
    def critical_with_context(self, msg: str, **context):
        """Critical log with context."""
        self.log_with_context(logging.CRITICAL, msg, context)


def configure_structured_logging(
    log_level: str = "INFO",
    include_console: bool = True
) -> None:
    """
    Configure application-wide structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_console: Whether to include console output
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    if include_console:
        # Console handler with structured formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        StructuredLogger instance with structured logging support
    """
    base_logger = logging.getLogger(name)
    return StructuredLogger(base_logger, {})


def set_request_id(request_id: str) -> None:
    """Set request ID for current context."""
    request_id_context.set(request_id)


def get_request_id() -> str:
    """Get current request ID."""
    return request_id_context.get()


def set_user_id(user_id: Optional[str]) -> None:
    """Set user ID for current context."""
    user_id_context.set(user_id)


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return user_id_context.get()


# Export public API
__all__ = [
    'StructuredFormatter',
    'StructuredLogger',
    'configure_structured_logging',
    'get_logger',
    'set_request_id',
    'get_request_id',
    'set_user_id',
    'get_user_id',
]
