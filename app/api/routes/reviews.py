from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.session import get_db
from app.models.review import Review
from app.schemas.review import ReviewCreate
from app.models.book import Book
from app.core.security import get_current_user

from app.services.ai_service import generate_review_summary



router = APIRouter()

@router.post("/books/{book_id}/reviews")
async def add_review(
    book_id: int,
    review: ReviewCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_review = Review(
        book_id=book_id,
        user_id=user["id"],
        review_text=review.review_text,
        rating=review.rating
    )
    db.add(new_review)
    await db.commit()
    return {"message": "Review added"}


@router.get("/books/{book_id}/reviews")
async def get_reviews(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.book_id == book_id)
    )
    return result.scalars().all()

@router.get("/books/{book_id}/reviews_summary")
async def book_summary(book_id: int, db: AsyncSession = Depends(get_db)):
    book_result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    rating_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.book_id == book_id)
    )
    avg_rating = rating_result.scalar()

    reviews_result = await db.execute(
        select(Review.review_text).where(Review.book_id == book_id)
    )
    reviews = [r[0] for r in reviews_result.all()]

    review_summary = ""
    if reviews:
        review_summary = await generate_review_summary(reviews)

    return {
        "book": book.title,
        "summary": book.summary,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "review_summary": review_summary
    }
