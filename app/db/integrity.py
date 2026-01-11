"""
Data integrity verification utilities for ORM layer.

This module provides functions to verify that cascade deletes worked correctly
and detect orphaned data that could indicate cascade failures.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, text
from app.models.book import Book
from app.models.review import Review
from app.models.user import User

logger = logging.getLogger(__name__)


async def check_orphaned_reviews(db: AsyncSession) -> dict:
    """
    Check for reviews referencing deleted books or users.
    
    Reviews become orphaned when:
    - Book is deleted but review still references it (book_id exists but book doesn't)
    - User is deleted but review still references it (user_id exists but user doesn't)
    
    Args:
        db: AsyncSession for database queries
        
    Returns:
        Dictionary with orphan counts and severity assessment
        
    Example:
        result = await check_orphaned_reviews(db)
        if result['has_orphans']:
            logger.error(f"Found {result['total_orphans']} orphaned reviews!")
    """
    try:
        # Reviews with missing books
        missing_books_result = await db.execute(
            select(func.count(Review.id)).where(
                ~Review.book_id.in_(
                    select(Book.id).select_from(Book)
                )
            )
        )
        missing_book_count = missing_books_result.scalar() or 0
        
        # Reviews with missing users
        missing_users_result = await db.execute(
            select(func.count(Review.id)).where(
                ~Review.user_id.in_(
                    select(User.id).select_from(User)
                )
            )
        )
        missing_user_count = missing_users_result.scalar() or 0
        
        total_orphans = missing_book_count + missing_user_count
        
        if total_orphans > 0:
            logger.error(
                f"Orphaned reviews detected: "
                f"{missing_book_count} missing books, {missing_user_count} missing users"
            )
        
        return {
            "has_orphans": total_orphans > 0,
            "orphaned_review_count": total_orphans,
            "reviews_with_missing_books": missing_book_count,
            "reviews_with_missing_users": missing_user_count,
            "severity": "CRITICAL" if total_orphans > 0 else "OK"
        }
        
    except Exception as e:
        logger.error(f"Error checking for orphaned reviews: {e}")
        return {
            "has_orphans": None,
            "error": str(e),
            "severity": "ERROR"
        }


async def check_orphaned_books(db: AsyncSession) -> dict:
    """
    Check for books referencing deleted users.
    
    Books become orphaned when user is deleted but book still references it.
    
    Args:
        db: AsyncSession for database queries
        
    Returns:
        Dictionary with orphan counts and severity assessment
    """
    try:
        # Books with missing users
        missing_users_result = await db.execute(
            select(func.count(Book.id)).where(
                ~Book.user_id.in_(
                    select(User.id).select_from(User)
                )
            )
        )
        orphan_count = missing_users_result.scalar() or 0
        
        if orphan_count > 0:
            logger.error(f"Orphaned books detected: {orphan_count} books with missing users")
        
        return {
            "has_orphans": orphan_count > 0,
            "orphaned_book_count": orphan_count,
            "severity": "CRITICAL" if orphan_count > 0 else "OK"
        }
        
    except Exception as e:
        logger.error(f"Error checking for orphaned books: {e}")
        return {
            "has_orphans": None,
            "error": str(e),
            "severity": "ERROR"
        }


async def run_full_integrity_check(db: AsyncSession) -> dict:
    """
    Run comprehensive data integrity check on all tables.
    
    Checks:
    - Orphaned reviews (missing books or users)
    - Orphaned books (missing users)
    - Constraint violations (ratings, years, roles)
    - Data consistency
    
    Args:
        db: AsyncSession for database queries
        
    Returns:
        Dictionary with full integrity status
    """
    logger.info("Running full database integrity check...")
    
    # Check orphaned reviews
    orphaned_reviews = await check_orphaned_reviews(db)
    
    # Check orphaned books
    orphaned_books = await check_orphaned_books(db)
    
    # Check constraint violations
    try:
        # Rating constraint: 1-5
        bad_ratings_result = await db.execute(
            select(func.count(Review.id)).where(
                (Review.rating < 1) | (Review.rating > 5)
            )
        )
        bad_ratings = bad_ratings_result.scalar() or 0
        
        # Year constraint: 1000-2100
        bad_years_result = await db.execute(
            select(func.count(Book.id)).where(
                (Book.year_published < 1000) | (Book.year_published > 2100)
            )
        )
        bad_years = bad_years_result.scalar() or 0
        
        # Role constraint: user or admin
        bad_roles_result = await db.execute(
            select(func.count(User.id)).where(
                ~User.role.in_(["user", "admin"])
            )
        )
        bad_roles = bad_roles_result.scalar() or 0
        
        constraint_violations = {
            "invalid_ratings": bad_ratings,
            "invalid_years": bad_years,
            "invalid_roles": bad_roles,
            "total_violations": bad_ratings + bad_years + bad_roles
        }
        
    except Exception as e:
        logger.error(f"Error checking constraints: {e}")
        constraint_violations = {"error": str(e)}
    
    # Determine overall status
    has_issues = (
        orphaned_reviews["has_orphans"] or 
        orphaned_books["has_orphans"] or 
        constraint_violations.get("total_violations", 0) > 0
    )
    
    status = {
        "overall_status": "CRITICAL" if has_issues else "OK",
        "orphaned_reviews": orphaned_reviews,
        "orphaned_books": orphaned_books,
        "constraint_violations": constraint_violations,
        "has_issues": has_issues
    }
    
    if has_issues:
        logger.error(f"Integrity check failed: {status}")
    else:
        logger.info("Integrity check passed: All data consistent")
    
    return status


async def verify_cascade_delete(
    db: AsyncSession,
    parent_type: str,
    parent_id: int,
    expected_orphans: int = 0
) -> dict:
    """
    Verify that a cascade delete operation succeeded.
    
    Args:
        db: AsyncSession for database queries
        parent_type: "user", "book", or "review"
        parent_id: ID of the deleted parent record
        expected_orphans: Expected number of orphaned children (should be 0)
        
    Returns:
        Dictionary with cascade verification results
    """
    if parent_type == "user":
        # Check orphaned books
        orphaned_books_result = await db.execute(
            select(func.count(Book.id)).where(Book.user_id == parent_id)
        )
        orphaned_books = orphaned_books_result.scalar() or 0
        
        # Check orphaned reviews by this user
        orphaned_reviews_result = await db.execute(
            select(func.count(Review.id)).where(Review.user_id == parent_id)
        )
        orphaned_reviews = orphaned_reviews_result.scalar() or 0
        
        cascade_successful = (orphaned_books == 0) and (orphaned_reviews == 0)
        
        return {
            "cascade_successful": cascade_successful,
            "parent_type": "user",
            "parent_id": parent_id,
            "orphaned_books": orphaned_books,
            "orphaned_reviews": orphaned_reviews,
            "expected_orphans": expected_orphans,
            "actual_orphans": orphaned_books + orphaned_reviews
        }
        
    elif parent_type == "book":
        # Check orphaned reviews
        orphaned_reviews_result = await db.execute(
            select(func.count(Review.id)).where(Review.book_id == parent_id)
        )
        orphaned_reviews = orphaned_reviews_result.scalar() or 0
        
        cascade_successful = orphaned_reviews == 0
        
        return {
            "cascade_successful": cascade_successful,
            "parent_type": "book",
            "parent_id": parent_id,
            "orphaned_reviews": orphaned_reviews,
            "expected_orphans": expected_orphans,
            "actual_orphans": orphaned_reviews
        }
        
    else:
        return {
            "error": f"Unknown parent_type: {parent_type}",
            "cascade_successful": False
        }
