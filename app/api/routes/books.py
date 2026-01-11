from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.core.security import require_admin, get_current_user
from app.core.structured_logging import get_logger, set_request_id
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.book import Book
from app.models.review import Review
from app.schemas.book import BookCreate, BookResponse
from app.services.ai_service import generate_book_summary
from app.services.summary_service import get_book_summary_data
from app.core.background_tasks import get_task_queue

logger = get_logger(__name__)

router = APIRouter()


@router.post("/books", response_model=BookResponse, status_code=201)
async def create_book(
    book: BookCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new book with AI-generated summary.
    
    Requires JWT authentication. Any authenticated user can create books.
    AI summary is generated asynchronously (or inline based on settings).
    """
    try:
        # Generate AI summary (with fallback) - kept inline for book creation UX
        logger.info_with_context(
            f"Creating book: {book.title}",
            book_title=book.title,
            user_id=user["id"]
        )
        summary = await generate_book_summary(book.model_dump())
    except Exception as e:
        # Log error but don't fail the request
        logger.error_with_context(
            f"Summary generation failed: {str(e)[:200]}",
            book_title=book.title,
            error=str(e)[:200]
        )
        summary = f"(Summary generation failed - {str(e)[:50]})"

    try:
        # Create book object
        new_book = Book(
            title=book.title,
            author=book.author,
            genre=book.genre,
            year_published=book.year_published,
            summary=summary,
            user_id=user["id"]
        )

        db.add(new_book)
        await db.commit()
        await db.refresh(new_book)
        
        logger.info_with_context(
            f"Book created: {new_book.id}",
            book_id=new_book.id,
            user_id=user["id"]
        )
        
        return new_book
        
    except IntegrityError as e:
        logger.error_with_context(
            "Database integrity error during book creation",
            book_title=book.title,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Book with this title by this author may already exist"
        )
    except Exception as e:
        logger.error_with_context(
            f"Failed to create book: {str(e)[:200]}",
            book_title=book.title,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create book"
        )


@router.get("/books", response_model=list[BookResponse])
async def get_all_books(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of books to return")
):
    """
    Get all books with pagination.
    
    Requires JWT authentication (any user).
    Supports skip and limit for pagination.
    """
    try:
        logger.info_with_context(
            "Fetching all books",
            skip=skip,
            limit=limit,
            user_id=current_user.get("id")
        )
        result = await db.execute(select(Book).offset(skip).limit(limit))
        books = result.scalars().all()
        logger.info_with_context(
            f"Returned {len(books)} books",
            count=len(books)
        )
        return books
    except Exception as e:
        logger.error_with_context(
            f"Failed to fetch books: {str(e)[:200]}",
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch books"
        )


@router.get("/books/{book_id}", response_model=BookResponse, dependencies=[Depends(require_admin)])
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific book by ID.
    
    Requires admin authentication.
    Returns 404 if book not found.
    """
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Fetching book: {book_id}",
            book_id=book_id
        )
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            logger.warning_with_context(
                f"Book not found: {book_id}",
                book_id=book_id
            )
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        
        return book
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to fetch book: {str(e)[:200]}",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch book"
        )


@router.put("/books/{book_id}", response_model=BookResponse, dependencies=[Depends(require_admin)])
async def update_book(
    book_id: int,
    data: BookCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing book.
    
    Requires admin authentication.
    Updates title, author, genre, and year_published fields.
    """
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Updating book: {book_id}",
            book_id=book_id
        )
        
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

        # Update fields
        book.title = data.title
        book.author = data.author
        book.genre = data.genre
        book.year_published = data.year_published

        await db.commit()
        await db.refresh(book)
        
        logger.info_with_context(
            f"Book updated: {book_id}",
            book_id=book_id
        )
        
        return book
    except IntegrityError as e:
        logger.error_with_context(
            "Database integrity error during book update",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Book update violates unique constraint"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to update book: {str(e)[:200]}",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update book"
        )


@router.delete("/books/{book_id}", dependencies=[Depends(require_admin)])
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a book.
    
    Requires admin authentication.
    Also deletes all associated reviews (cascade).
    
    Returns count of cascaded deletes and verification status.
    """
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Deleting book: {book_id}",
            book_id=book_id
        )
        
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

        # Count associated reviews before deletion
        reviews_result = await db.execute(
            select(func.count(Review.id)).where(Review.book_id == book_id)
        )
        review_count = reviews_result.scalar() or 0

        # Delete book (cascades to reviews)
        await db.delete(book)
        await db.commit()
        
        # Verify cascade worked
        orphan_result = await db.execute(
            select(func.count(Review.id)).where(Review.book_id == book_id)
        )
        orphaned_reviews = orphan_result.scalar() or 0
        
        if orphaned_reviews > 0:
            logger.error_with_context(
                f"Cascade delete failed for book {book_id}: {orphaned_reviews} reviews still exist",
                book_id=book_id,
                orphaned_count=orphaned_reviews
            )
        
        logger.info_with_context(
            f"Book deleted: {book_id} (cascaded {review_count} reviews)",
            book_id=book_id,
            review_count=review_count
        )
        
        return {
            "message": f"Book {book_id} deleted successfully",
            "reviews_cascaded": review_count,
            "cascade_verification": {
                "orphaned_reviews": orphaned_reviews,
                "cascade_successful": orphaned_reviews == 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to delete book: {str(e)[:200]}",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete book"
        )


@router.post("/generate-summary", dependencies=[Depends(require_admin)])
async def generate_summary(payload: BookCreate):
    """
    Generate AI summary for a book (async background task).
    
    Requires admin authentication.
    Accepts book data and returns task ID for polling.
    """
    try:
        logger.info_with_context(
            f"Submitting summary generation task for: {payload.title}",
            book_title=payload.title
        )
        
        task_queue = get_task_queue()
        task_id = await task_queue.submit("generate_book_summary", payload.model_dump())
        
        return {
            "task_id": task_id,
            "message": "Summary generation started",
            "status_url": f"/tasks/{task_id}"
        }
    except Exception as e:
        logger.error_with_context(
            f"Failed to submit summary task: {str(e)[:200]}",
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit task"
        )


@router.get("/books/{book_id}/summary", response_model=dict, dependencies=[Depends(require_admin)])
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive book summary with review analysis.
    
    Requires admin authentication.
    Returns book metadata, average rating, and AI review summary.
    """
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Fetching summary for book: {book_id}",
            book_id=book_id
        )
        
        data = await get_book_summary_data(book_id, db)

        if not data:
            logger.warning_with_context(
                f"Book summary not found: {book_id}",
                book_id=book_id
            )
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

        logger.info_with_context(
            f"Summary retrieved for book: {book_id}",
            book_id=book_id
        )
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to fetch summary: {str(e)[:200]}",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch summary"
        )
