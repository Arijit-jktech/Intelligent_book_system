from pydantic import BaseModel

class ReviewCreate(BaseModel):
    review_text: str
    rating: int
