import os
import logging
import sys
import warnings
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Optional

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)

# Configuration from environment variables
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# SECURITY: All secrets must be set via environment variables in production
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production-use-32-char-minimum")

if not SECRET_KEY or SECRET_KEY == "dev-key-change-in-production-use-32-char-minimum":
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        logger.critical(
            "🔓 CRITICAL SECURITY: SECRET_KEY not properly configured for production! "
            "Set SECRET_KEY environment variable to a strong random value. "
            "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
        sys.exit(1)
    warnings.warn(
        "⚠️  Using development SECRET_KEY. Change to a strong random value in production!",
        RuntimeWarning
    )

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "1"))

# Allowed roles in the system
ALLOWED_ROLES = {"user", "admin"}


# ============================================================================
# PASSWORD HASHING AND VERIFICATION
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using Argon2 or bcrypt.
    Enforces 72-byte limit for bcrypt compatibility.
    
    Args:
        password: Plaintext password
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password exceeds 72 bytes
    """
    if isinstance(password, str):
        b = password.encode("utf-8")
    else:
        b = bytes(password)

    if len(b) > 72:
        raise ValueError(
            "Password cannot be longer than 72 bytes when using bcrypt. "
            f"Got {len(b)} bytes."
        )

    hashed = pwd_context.hash(password)
    logger.debug("Password hashed successfully")
    return hashed


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a hash.
    
    Args:
        plain: Plaintext password
        hashed: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        result = pwd_context.verify(plain, hashed)
        if not result:
            logger.debug("Password verification failed")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================================================
# JWT TOKEN GENERATION AND VERIFICATION
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary with user info (sub, role, id)
        expires_delta: Custom expiration time (default: TOKEN_EXPIRE_HOURS)
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"JWT token created with expiry: {expire}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token encoding failed: {e}")
        raise


def decode_access_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        raise


# ============================================================================
# AUTHENTICATION AND AUTHORIZATION
# ============================================================================

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User payload with id, role, sub (username)
        
    Raises:
        HTTPException: If token is invalid or missing required fields
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        
        # Validate required fields
        if not username or user_id is None or not role:
            logger.warning("Token missing required fields")
            raise credentials_exception
        
        # Validate role
        if role not in ALLOWED_ROLES:
            logger.warning(f"Token contains invalid role: {role}")
            raise credentials_exception
        
        return {
            "id": user_id,
            "username": username,
            "role": role
        }
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception


def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    """
    Verify user has admin role.
    
    Args:
        user: Current user from get_current_user
        
    Returns:
        User object if authorized
        
    Raises:
        HTTPException: If user is not admin
    """
    if user.get("role") != "admin":
        logger.warning(f"Unauthorized admin access attempt by user {user.get('id')} with role {user.get('role')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def require_user(user: Dict = Depends(get_current_user)) -> Dict:
    """
    Verify user has user or admin role (any authenticated user).
    
    Args:
        user: Current user from get_current_user
        
    Returns:
        User object if authorized
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if user.get("role") not in ALLOWED_ROLES:
        logger.warning(f"Unauthorized access attempt by invalid role: {user.get('role')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required"
        )
    return user
