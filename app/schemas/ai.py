"""
Schemas for AI-generated summaries and structured outputs.
These provide type-safe, validated responses from LLM calls.
"""
from pydantic import BaseModel, Field
from typing import Optional


class BookSummary(BaseModel):
    """Structured response for book summaries."""
    summary: str = Field(
        ..., 
        description="Concise professional summary of the book",
        max_length=2000
    )
    key_themes: list[str] = Field(
        default_factory=list,
        description="Main themes or topics covered",
        max_items=10
    )
    target_audience: Optional[str] = Field(
        None,
        description="Intended audience for the book",
        max_length=200
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "A comprehensive guide to modern Python development...",
                "key_themes": ["Python", "Best Practices", "Async Programming"],
                "target_audience": "Intermediate Python developers"
            }
        }


class ReviewSummary(BaseModel):
    """Structured response for review analysis."""
    overall_sentiment: str = Field(
        ...,
        description="Overall sentiment: positive, negative, or neutral",
        pattern="^(positive|negative|neutral)$"
    )
    summary: str = Field(
        ...,
        description="Concise summary of all reviews",
        max_length=2000
    )
    positives: list[str] = Field(
        default_factory=list,
        description="Common positive points from reviewers",
        max_items=5
    )
    negatives: list[str] = Field(
        default_factory=list,
        description="Common criticisms or negative points",
        max_items=5
    )
    recommendation_score: float = Field(
        ...,
        description="Overall recommendation score 0-10",
        ge=0,
        le=10
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall_sentiment": "positive",
                "summary": "Readers praised the detailed examples and clear explanations...",
                "positives": ["Clear examples", "Well-structured", "Practical"],
                "negatives": ["Advanced topics lacking detail", "Expensive"],
                "recommendation_score": 8.5
            }
        }


class ModelConfig(BaseModel):
    """Configuration for model behavior."""
    temperature: float = Field(
        0.7,
        description="Temperature for generation (0.0-1.0). Lower = deterministic, Higher = creative",
        ge=0,
        le=1
    )
    top_p: float = Field(
        0.9,
        description="Nucleus sampling parameter (0.0-1.0)",
        ge=0,
        le=1
    )
    top_k: int = Field(
        40,
        description="Top-k sampling",
        ge=0
    )
    num_predict: int = Field(
        256,
        description="Maximum tokens to generate",
        ge=1,
        le=4096
    )
    repeat_penalty: float = Field(
        1.1,
        description="Penalty for repeating tokens (1.0 = no penalty)",
        ge=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 256,
                "repeat_penalty": 1.1
            }
        }
