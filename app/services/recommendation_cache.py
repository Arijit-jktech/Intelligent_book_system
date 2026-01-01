from app.services.recommendation_service import get_recommendations
from app.core.cache import redis_client
import json
import logging

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 hour

def cache_key(genre: str):
    return f"recommendations:{genre.lower()}"

async def get_recommendations_with_cache(
    genre: str,
    db
):
    key = cache_key(genre)

    cached = await redis_client.get(key)

    if cached:
        try:
            data = json.loads(cached)
            if isinstance(data, list) and len(data) > 0:
                print("Cache HIT")
                return data
        except json.JSONDecodeError:
            await redis_client.delete(key)

    # Cache MISS (None OR empty list)
    data = await get_recommendations(genre, db)
    await redis_client.setex(key, CACHE_TTL, json.dumps(data))
    return data
                

        

        

    
        
