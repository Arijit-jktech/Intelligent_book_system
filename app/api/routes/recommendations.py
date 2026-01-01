from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.core.security import require_admin
from app.services.recommendation_cache import get_recommendations_with_cache

router = APIRouter()


class RecommendationRequest(BaseModel):
    genre: str


@router.post("/recommendations", response_model=dict, dependencies=[Depends(require_admin)])
async def recommend_books(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get book recommendations based on genre. Requires admin authentication.
    
    Request body:
    {
        "genre": "science fiction"
    }
    """
    recommendations = await get_recommendations_with_cache(request.genre, db)
    return {
        "genre": request.genre,
        "recommendations": recommendations
    }
