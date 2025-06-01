"""
User-related Pydantic schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models.user import UserType
from models.professional_bridge import TherapyModality


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    user_type: UserType = UserType.CLIENT


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

    # Inner Ally Agent preferences
    agent_persona: str = Field(default="gentle_mentor", pattern="^(gentle_mentor|warm_friend|wise_elder|custom)$")
    custom_persona_name: Optional[str] = None
    custom_persona_description: Optional[str] = None
    favorite_affirmations: Optional[List[str]] = None
    preferred_coping_styles: Optional[List[str]] = None
    crisis_contact_enabled: bool = True
    widget_enabled: bool = True
    micro_checkin_frequency: int = Field(default=4, ge=1, le=24)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
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


class TherapistRegistration(BaseModel):
    """Schema for therapist registration."""
    # User fields
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)

    # Therapist profile fields
    phone: Optional[str] = None
    license_number: str = Field(..., min_length=5, max_length=50)
    credentials: List[str] = Field(..., min_items=1)
    specialties: List[TherapyModality] = Field(..., min_items=1)
    years_experience: int = Field(..., ge=0, le=50)
    bio: Optional[str] = Field(None, max_length=2000)
    hourly_rate: float = Field(..., ge=0.0, le=1000.0)
    accepts_insurance: bool = False
    insurance_providers: Optional[List[str]] = None
    timezone: str = Field(default="UTC")
