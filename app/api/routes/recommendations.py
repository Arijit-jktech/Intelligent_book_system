from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.core.security import require_admin
from app.services.recommendation_cache import get_recommendations_with_cache

router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request schema for book recommendations."""
    genre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Genre to get recommendations for"
    )


@router.post("/recommendations", response_model=dict, dependencies=[Depends(require_admin)])
async def recommend_books(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(5, ge=1, le=50, description="Max recommendations to return")
):
    """
    Get book recommendations by genre.
    
    Requires admin authentication.
    Uses Redis caching for performance.
    """
    # Validate genre
    if not request.genre.strip():
        raise HTTPException(status_code=400, detail="Genre cannot be empty")
    
    try:
        # Get recommendations (cached)
        recommendations = await get_recommendations_with_cache(
            request.genre.strip().lower(),
            db
        )
        
        # Apply limit
        recommendations = recommendations[:limit]
        
        return {
            "genre": request.genre,
            "count": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)[:100]}"
        )
