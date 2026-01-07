"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.models.user import UserRole


# ===== User Schemas =====

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str
    role: UserRole


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    is_active: bool
    avatar: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Auth Schemas =====

class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


# ===== Generic Schemas =====

class ApiResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: dict
