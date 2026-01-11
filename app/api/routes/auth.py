from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import logging
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
    require_admin,
    ALLOWED_ROLES
)
from app.schemas.auth import LoginRequest, TokenResponse, SignupRequest, UserResponse
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user account",
    description="Registers a new user with a unique username and hashed password."
)
async def signup(
    credentials: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user account.
    
    - **username**: Must be 3-50 characters, alphanumeric with underscore/hyphen
    - **password**: Must be 8+ characters with at least one digit
    - **role**: Either "user" (default) or "admin"
    
    Returns the created user (without password) on success.
    """
    # Normalize username
    username = credentials.username.lower().strip()
    
    # Check if username already exists
    existing = await db.execute(
        select(User).where(User.username == username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{credentials.username}' already exists"
        )

    # Validate role
    if credentials.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(ALLOWED_ROLES)}"
        )

    # Hash password - will raise ValueError if too long
    try:
        hashed = hash_password(credentials.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    # Create user
    orm_user = User(
        username=username,
        password=hashed,
        role=credentials.role.lower()
    )
    
    db.add(orm_user)
    await db.commit()
    await db.refresh(orm_user)
    
    return orm_user

    
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT token",
    description="Validates user credentials and returns a JWT access token."
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with username and password.
    
    Returns a JWT access token on successful authentication.
    
    Errors:
    - 401: Invalid username or password
    """
    # Normalize username
    username = credentials.username.lower().strip()
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    # Check user exists and password matches
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Create JWT token
    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "id": user.id
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.delete(
    "/{user_id}",
    status_code=200,
    summary="Delete a user account (admin only)",
    description="Deletes a user and cascades deletion to all associated books and reviews."
)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    admin_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user account and all associated data.
    
    **Admin-only endpoint**
    
    Cascading deletes:
    - All books owned by the user
    - All reviews written by the user
    - All reviews on books owned by the user
    
    Returns count of deleted records and cascade verification status.
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must be positive"
        )
    
    # Fetch user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Count associated records before deletion
    books_result = await db.execute(
        select(func.count(Book.id)).where(Book.user_id == user_id)
    )
    book_count = books_result.scalar() or 0
    
    reviews_result = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == user_id)
    )
    review_count = reviews_result.scalar() or 0
    
    # Delete user (cascades to books and reviews)
    await db.delete(user)
    await db.commit()
    
    # Verify cascade worked
    orphan_books = await db.execute(
        select(func.count(Book.id)).where(Book.user_id == user_id)
    )
    orphan_book_count = orphan_books.scalar() or 0
    
    orphan_reviews = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == user_id)
    )
    orphan_review_count = orphan_reviews.scalar() or 0
    
    if orphan_book_count > 0 or orphan_review_count > 0:
        logger.error(
            f"Cascade delete failed for user {user_id}: "
            f"{orphan_book_count} orphaned books, {orphan_review_count} orphaned reviews"
        )
    
    return {
        "message": f"User {user_id} deleted successfully with all associated data",
        "books_deleted": book_count,
        "reviews_authored_deleted": review_count,
        "cascade_verification": {
            "orphaned_books": orphan_book_count,
            "orphaned_reviews": orphan_review_count
        }
    }
