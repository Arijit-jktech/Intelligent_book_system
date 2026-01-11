from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ReviewCreate(BaseModel):
    """Schema for creating a new review."""
    review_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Review text (10-5000 characters)"
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 to 5 stars"
    )

    @field_validator('review_text')
    @classmethod
    def validate_review_text(cls, v):
        """Validate review doesn't contain only whitespace."""
        if not v.strip():
            raise ValueError('Review text cannot be empty or whitespace-only')
        return v.strip()


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: int
    book_id: int
    user_id: int
    review_text: str
    rating: int

    class Config:
        from_attributes = True
