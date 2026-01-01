from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import LoginRequest, TokenResponse, SignupRequest, UserResponse
from app.models.user import User
from app.db.session import get_db

router = APIRouter()

@router.post("/signup",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user account",
    description="Registers a new user with a unique username and hashed password.")
async def signup(credentials: SignupRequest,db: AsyncSession = Depends(get_db)):
    """
    Signup endpoint - accepts JSON payload with username, password and role.
    
    Example request body:
    {
        "username": "any_username",
        "password": "any_password", # You may want to enforce password policies in production
        "role": "admin"  # or "user"
    }
    """
    # Check uniqueness: username must be unique
    existing = await db.execute(select(User).where(User.username == credentials.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash password before storing — handle bcrypt 72-byte limit
    try:
        hashed = hash_password(credentials.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    orm_user = User(
        username=credentials.username,
        password=hashed,
        role=credentials.role
    )
    db.add(orm_user)
    await db.commit()
    await db.refresh(orm_user)
    # Return the ORM user; FastAPI will serialize using UserResponse
    return orm_user
    

@router.post("/login", 
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT token",
    description="Validates user credentials and returns a JWT access token.")
async def login(credentials: LoginRequest,db: AsyncSession = Depends(get_db)):
    """
    Login endpoint - accepts JSON payload with username and password.
    
    Example request body:
    {
        "username": "username_here",
        "password": "password_here"
    }
    """
    # Fetch user from DB
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "id": user.id
    })

    return {"access_token": token, "token_type": "bearer"}
