from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import require_admin, get_current_user
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.book import Book
from app.schemas.book import BookCreate, BookResponse
from app.services.ai_service import generate_book_summary

from sqlalchemy import func
from app.models.review import Review
from app.services.summary_service import get_book_summary_data




router = APIRouter()

@router.post("/books", response_model=BookResponse)
async def create_book(book: BookCreate, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    summary = await generate_book_summary(book.dict())

    new_book = Book(
        **book.dict(),
        summary=summary,
        user_id=user["id"]
    )

    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book


@router.get("/books", response_model=list[BookResponse])
async def get_all_books(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all books - requires JWT authentication but not admin role or
    If Required You can add filter for books creted by the login user."""
    result = await db.execute(select(Book))
    return result.scalars().all()


@router.get("/books/{book_id}", response_model=BookResponse, dependencies=[Depends(require_admin)])
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/books/{book_id}", response_model=BookResponse, dependencies=[Depends(require_admin)])
async def update_book(book_id: int, data: BookCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for key, value in data.dict().items():
        setattr(book, key, value)

    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/books/{book_id}", dependencies=[Depends(require_admin)])
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    await db.delete(book)
    await db.commit()
    return {"message": "Book deleted successfully"}

@router.post("/generate-summary", dependencies=[Depends(require_admin)])
async def generate_summary(payload: dict):
    summary = await generate_book_summary(payload)
    return {"summary": summary}

@router.get("/books/{book_id}/summary", response_model=dict,dependencies=[Depends(require_admin)])
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    data = await get_book_summary_data(book_id, db)

    if not data:
        raise HTTPException(status_code=404, detail="Book not found")

    return data
