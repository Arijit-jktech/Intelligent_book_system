from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class LoginRequest(BaseModel):
    """Schema for user login."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters)"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Password (minimum 6 characters)"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username can only contain alphanumeric, underscore, and hyphen')
        return v.lower().strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password is not just whitespace."""
        if not v.strip():
            raise ValueError('Password cannot be empty or whitespace')
        return v


class SignupRequest(BaseModel):
    """Schema for user registration."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters, alphanumeric + underscore/hyphen)"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (minimum 8 characters for signup)"
    )
    role: Literal["user", "admin"] = Field(
        "user",
        description="User role: 'user' or 'admin' (default: 'user')"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format and prevent reserved names."""
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username can only contain alphanumeric, underscore, and hyphen')
        # Prevent reserved usernames
        reserved = {'admin', 'root', 'system', 'test', 'guest'}
        if v.lower() in reserved:
            raise ValueError(f'Username "{v}" is reserved')
        return v.lower().strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if not v.strip():
            raise ValueError('Password cannot be empty or whitespace')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        # Optional: Require complexity (at least one digit)
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is allowed value."""
        if v not in ("user", "admin"):
            raise ValueError('Role must be "user" or "admin"')
        return v.lower()


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        "bearer",
        description="Token type (always 'bearer')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

