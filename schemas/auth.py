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
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class UserOut(BaseModel):
    """Schema for user output"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool = True
    
    class Config:
        from_attributes = True
