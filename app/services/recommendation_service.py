from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.book import Book
from app.models.review import Review

async def get_recommendations(
    genre: str,
    db: AsyncSession,
    limit: int = 5
):  
    books = await db.execute(select(Book))
    books = books.scalars().all()
    for book in books:
        print(book.id, book.title, book.genre)

    reviews = await db.execute(select(Review))
    reviews = reviews.scalars().all()
    for review in reviews:
        print(review.id, review.book_id, review.rating)

    stmt = (
    select(
        Book.id,
        Book.title,
        Book.author,
        Book.genre,
        func.avg(Review.rating).label("avg_rating")
        )
        .join(Review, Review.book_id == Book.id)
        .where(
            func.lower(func.trim(Book.genre)) ==
            func.lower(func.trim(genre))
        )
        .group_by(Book.id)
        .having(func.avg(Review.rating) >= 4)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    return [
        {
            "book_id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "genre": row["genre"],
            "avg_rating": round(row["avg_rating"], 2)
        }
        for row in rows
    ]
