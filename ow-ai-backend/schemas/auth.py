"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class LoginInput(BaseModel):
    """
    Schema for user login - JSON format
    Accepts: {"email": "user@example.com", "password": "password"}
    """
    email: EmailStr = Field(
        ...,
        description="User email address",
        json_schema_extra={"example": "user@owkai.com"}
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password",
        json_schema_extra={"example": "SecurePassword123!"}
    )


class TokenResponse(BaseModel):
    """
    Schema for authentication token response
    Supports both bearer tokens and cookie-based authentication
    """
    access_token: str = Field(
        ...,
        description="JWT access token (empty string for cookie mode)"
    )
    token_type: str = Field(
        default="bearer",
        description="Authentication type: 'bearer' or 'cookie'"
    )
    expires_in: Optional[int] = Field(
        default=None,
        description="Token expiration time in seconds"
    )
    refresh_token: Optional[str] = Field(
        default="",
        description="JWT refresh token (empty string for cookie mode)"
    )


class UserOut(BaseModel):
    """Schema for user output"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool = True
    
    class Config:
        from_attributes = True
