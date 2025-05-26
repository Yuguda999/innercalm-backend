"""
User-related Pydantic schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for user profile update."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserPreferences(BaseModel):
    """Schema for user preferences."""
    theme: str = Field(default="light", pattern="^(light|dark)$")
    daily_reminders: bool = True
    weekly_reports: bool = True
    recommendations: bool = True
    achievements: bool = False
    language: str = Field(default="en", max_length=5)
    timezone: str = Field(default="UTC", max_length=50)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None
