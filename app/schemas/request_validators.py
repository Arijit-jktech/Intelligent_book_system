"""
Request Validation Schemas
Enhanced validation for request bodies and query parameters.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import html


class RequestValidationConfig(BaseModel):
    """Global request validation configuration."""
    
    max_body_size: int = 1_048_576  # 1MB
    max_string_length: int = 10_000
    max_search_length: int = 200
    max_array_length: int = 1_000
    max_review_length: int = 5_000
    min_review_length: int = 10


class SanitizedString(str):
    """String that auto-sanitizes dangerous characters."""
    
    @staticmethod
    def sanitize(value: str) -> str:
        """Remove potential XSS and injection payloads."""
        # HTML encode dangerous characters
        value = html.escape(value)
        # Remove null bytes
        value = value.replace('\x00', '')
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        return value
    
    def __new__(cls, value: str):
        """Create sanitized string."""
        if not isinstance(value, str):
            raise ValueError("SanitizedString must be a string")
        sanitized = cls.sanitize(value)
        return str.__new__(cls, sanitized)


class EnhancedReviewCreate(BaseModel):
    """Enhanced review creation with comprehensive validation."""
    
    review_text: str = Field(
        ...,
        min_length=10,  # At least 10 characters
        max_length=5000,  # No more than 5000 characters
        description="Review text (10-5000 characters)"
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 to 5"
    )
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('review_text')
    @classmethod
    def validate_review_text(cls, v: str) -> str:
        """Validate review text format and content."""
        if not v or not v.strip():
            raise ValueError('Review cannot be empty or whitespace-only')
        
        if len(v.strip()) < 10:
            raise ValueError('Review must be at least 10 characters')
        
        if len(v) > 5000:
            raise ValueError('Review cannot exceed 5000 characters')
        
        # Check for excessive repetition (spam detection)
        if _is_spam(v):
            raise ValueError('Review appears to be spam (excessive repetition)')
        
        return v.strip()
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: int) -> int:
        """Validate rating value."""
        if not isinstance(v, int):
            raise ValueError('Rating must be an integer')
        
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        
        return v


class SearchQueryValidator(BaseModel):
    """Validator for search query parameters."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query (1-200 characters)"
    )
    skip: int = Field(
        default=0,
        ge=0,
        le=100_000,
        description="Number of results to skip"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results to return"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        
        if len(v) > 200:
            raise ValueError('Query cannot exceed 200 characters')
        
        return v.strip()


class PaginationValidator(BaseModel):
    """Validator for pagination parameters."""
    
    skip: int = Field(
        default=0,
        ge=0,
        le=1_000_000,
        description="Number of records to skip"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=1_000,
        description="Number of records to return"
    )
    
    @field_validator('skip', 'limit')
    @classmethod
    def validate_pagination(cls, v: int) -> int:
        """Validate pagination values."""
        if not isinstance(v, int):
            raise ValueError('Pagination values must be integers')
        
        if v < 0:
            raise ValueError('Pagination values cannot be negative')
        
        return v


def _is_spam(text: str, repeat_threshold: float = 0.5) -> bool:
    """
    Detect obvious spam patterns.
    
    Args:
        text: Text to check
        repeat_threshold: Threshold for character repetition (0.0-1.0)
    
    Returns:
        True if text appears to be spam
    """
    if not text or len(text) < 10:
        return False
    
    # Check for excessive character repetition
    max_char_count = max(text.count(char) for char in set(text))
    if max_char_count / len(text) > repeat_threshold:
        return True
    
    # Check for repeated words
    words = text.split()
    if len(words) > 0:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        if max(word_counts.values()) / len(words) > repeat_threshold:
            return True
    
    return False


__all__ = [
    'RequestValidationConfig',
    'SanitizedString',
    'EnhancedReviewCreate',
    'SearchQueryValidator',
    'PaginationValidator',
]
