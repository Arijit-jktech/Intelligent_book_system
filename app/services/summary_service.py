from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.book import Book
from app.models.review import Review
from app.services.ai_service import generate_review_summary


async def get_book_summary_data(
    book_id: int,
    db: AsyncSession
):
    # Fetch book
    book_result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = book_result.scalar_one_or_none()

    if not book:
        return None

    # Aggregated rating
    rating_result = await db.execute(
        select(
            func.avg(Review.rating),
            func.count(Review.id)
        ).where(Review.book_id == book_id)
    )
    avg_rating, review_count = rating_result.one()

    # Fetch reviews text
    reviews_result = await db.execute(
        select(Review.review_text)
        .where(Review.book_id == book_id)
        .where(Review.review_text.isnot(None))
    )
    reviews = [row[0] for row in reviews_result.all()]

    review_insights = None
    if reviews:
        review_insights = await generate_review_summary(reviews)

    return {
        "book_id": book.id,
        "title": book.title,
        "author": book.author,
        "genre": book.genre,
        "year_published": book.year_published,
        "book_summary": book.summary,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "total_reviews": review_count,
        "review_insights": review_insights
    }
