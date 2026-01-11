from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.session import get_db
from app.models.review import Review
from app.models.book import Book
from app.schemas.review import ReviewCreate, ReviewResponse
from app.core.security import get_current_user, require_admin
from app.services.ai_service import generate_review_summary
from app.core.structured_logging import get_logger
from app.schemas.request_validators import EnhancedReviewCreate

logger = get_logger(__name__)

router = APIRouter()


@router.post("/books/{book_id}/reviews", response_model=dict, status_code=201)
async def add_review(
    book_id: int,
    review: EnhancedReviewCreate,  # Enhanced validation
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a review to a book.
    
    Requires JWT authentication.
    Validates book exists and review content (10-5000 chars, rating 1-5).
    """
    # Validate book ID
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Adding review to book {book_id}",
            book_id=book_id,
            user_id=user["id"],
            rating=review.rating
        )
        
        # Check book exists
        book_result = await db.execute(select(Book).where(Book.id == book_id))
        book = book_result.scalar_one_or_none()
        if not book:
            logger.warning_with_context(
                f"Book not found for review: {book_id}",
                book_id=book_id
            )
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        
        # Create review
        new_review = Review(
            book_id=book_id,
            user_id=user["id"],
            review_text=review.review_text,
            rating=review.rating
        )
        
        db.add(new_review)
        await db.commit()
        await db.refresh(new_review)
        
        logger.info_with_context(
            f"Review created: {new_review.id}",
            review_id=new_review.id,
            book_id=book_id,
            user_id=user["id"]
        )
        
        return {"message": "Review added successfully", "review_id": new_review.id}
    
    except IntegrityError as e:
        logger.error_with_context(
            "Database integrity error during review creation",
            book_id=book_id,
            user_id=user["id"],
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You may have already reviewed this book"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to add review: {str(e)[:200]}",
            book_id=book_id,
            user_id=user["id"],
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add review"
        )


@router.get("/books/{book_id}/reviews", response_model=list[ReviewResponse])
async def get_reviews(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of reviews to return")
):
    """
    Get reviews for a book.
    
    Public endpoint (no auth required).
    Supports pagination via skip and limit.
    """
    # Validate book ID
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Fetching reviews for book {book_id}",
            book_id=book_id,
            skip=skip,
            limit=limit
        )
        
        # Check book exists
        book_result = await db.execute(select(Book).where(Book.id == book_id))
        if not book_result.scalar_one_or_none():
            logger.warning_with_context(
                f"Book not found: {book_id}",
                book_id=book_id
            )
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        
        # Get reviews with pagination
        result = await db.execute(
            select(Review)
            .where(Review.book_id == book_id)
            .offset(skip)
            .limit(limit)
        )
        reviews = result.scalars().all()
        
        logger.info_with_context(
            f"Returned {len(reviews)} reviews for book {book_id}",
            book_id=book_id,
            count=len(reviews)
        )
        
        return reviews
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to fetch reviews: {str(e)[:200]}",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reviews"
        )


@router.get("/books/{book_id}/reviews_summary", response_model=dict, dependencies=[Depends(require_admin)])
async def get_reviews_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-generated summary of all reviews for a book.
    
    🔐 ADMIN ONLY - AI summary generation is resource-intensive.
    Requires JWT authentication with admin role.
    Includes book metadata, average rating, and AI analysis.
    """
    # Validate book ID
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Book ID must be positive")
    
    try:
        logger.info_with_context(
            f"Fetching review summary for book {book_id}",
            book_id=book_id
        )
        
        # Get book
        book_result = await db.execute(select(Book).where(Book.id == book_id))
        book = book_result.scalar_one_or_none()
        if not book:
            logger.warning_with_context(
                f"Book not found: {book_id}",
                book_id=book_id
            )
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

        # Get average rating and count
        rating_result = await db.execute(
            select(
                func.avg(Review.rating),
                func.count(Review.id)
            ).where(Review.book_id == book_id)
        )
        avg_rating, review_count = rating_result.one()

        # Get review texts
        reviews_result = await db.execute(
            select(Review.review_text)
            .where(Review.book_id == book_id)
            .where(Review.review_text.isnot(None))
        )
        reviews = [r[0] for r in reviews_result.all()]

        # Generate AI summary if reviews exist
        review_summary = ""
        if reviews:
            try:
                logger.info_with_context(
                    f"Generating AI summary for {len(reviews)} reviews",
                    book_id=book_id,
                    review_count=len(reviews)
                )
                review_summary = await generate_review_summary(reviews)
            except Exception as e:
                logger.error_with_context(
                    f"Summary generation failed: {str(e)[:200]}",
                    book_id=book_id,
                    error=str(e)[:200]
                )
                review_summary = f"(Summary generation failed - {str(e)[:50]})"
        
        result_data = {
            "book_id": book.id,
            "book": book.title,
            "author": book.author,
            "summary": book.summary,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "total_reviews": review_count or 0,
            "review_summary": review_summary
        }
        
        logger.info_with_context(
            f"Review summary retrieved for book {book_id}",
            book_id=book_id,
            review_count=review_count
        )
        
        return result_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error_with_context(
            f"Failed to fetch review summary: {str(e)[:200]}",
            book_id=book_id,
            error=str(e)[:200]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch review summary"
        )
