from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional


class BookCreate(BaseModel):
    """Schema for creating/updating books."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Book title"
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Author name"
    )
    genre: Optional[str] = Field(
        None,
        max_length=100,
        description="Book genre"
    )
    year_published: Optional[int] = Field(
        None,
        ge=1000,
        le=2100,
        description="Year published (1000-2100)"
    )

    @field_validator('title', 'author')
    @classmethod
    def validate_non_empty(cls, v):
        """Validate fields are not just whitespace."""
        if not v.strip():
            raise ValueError('Field cannot be empty or whitespace-only')
        return v.strip()

    @field_validator('genre')
    @classmethod
    def validate_genre(cls, v):
        """Validate genre if provided."""
        if v is not None and not v.strip():
            raise ValueError('Genre cannot be whitespace-only')
        return v.strip() if v else None


class BookResponse(BookCreate):
    """Schema for book response."""
    id: int
    user_id: int
    summary: Optional[str] = Field(
        None,
        description="AI-generated or fallback summary"
    )

    model_config = ConfigDict(from_attributes=True)
