from pydantic import BaseModel, ConfigDict
from typing import Optional

class BookCreate(BaseModel):
    title: str
    author: str
    genre: Optional[str]
    year_published: Optional[int]

class BookResponse(BookCreate):
    id: int
    user_id: int
    summary: Optional[str]

    model_config = ConfigDict(from_attributes=True)