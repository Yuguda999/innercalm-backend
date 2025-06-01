"""
Authentication service for user management and JWT tokens.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.user import User, UserType
from models.professional_bridge import TherapistProfile
from schemas.user import UserCreate, TokenData, TherapistRegistration
from config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for user authentication and authorization."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
            
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return TokenData(username=username)
        except JWTError as e:
            logger.error(f"JWT error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username or email and password."""
        try:
            # Try to find user by username first, then by email
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = db.query(User).filter(User.email == username).first()

            if not user:
                return None
            if not AuthService.verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get a user by username."""
        try:
            return db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Check if user already exists
            if AuthService.get_user_by_username(db, user_data.username):
                raise ValueError("Username already exists")
            
            if AuthService.get_user_by_email(db, user_data.email):
                raise ValueError("Email already exists")
            
            # Create new user
            hashed_password = AuthService.get_password_hash(user_data.password)
            db_user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                full_name=user_data.full_name
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"Created new user: {user_data.username}")
            return db_user
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def update_user_activity(db: Session, user_id: int) -> None:
        """Update user's last activity timestamp."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
            db.rollback()

    @staticmethod
    def create_therapist(db: Session, therapist_data: TherapistRegistration) -> User:
        """Create a new therapist user with profile."""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == therapist_data.email) |
                (User.username == therapist_data.username)
            ).first()
            if existing_user:
                raise ValueError("User with this email or username already exists")

            # Check if license number already exists
            existing_license = db.query(TherapistProfile).filter(
                TherapistProfile.license_number == therapist_data.license_number
            ).first()
            if existing_license:
                raise ValueError("Therapist with this license number already exists")

            # Create user
            hashed_password = AuthService.get_password_hash(therapist_data.password)
            user = User(
                email=therapist_data.email,
                username=therapist_data.username,
                hashed_password=hashed_password,
                full_name=therapist_data.full_name,
                user_type=UserType.THERAPIST,
                is_verified=False  # Therapists need verification
            )
            db.add(user)
            db.flush()  # Get user ID

            # Create therapist profile
            therapist_profile = TherapistProfile(
                user_id=user.id,
                full_name=therapist_data.full_name,
                email=therapist_data.email,
                phone=therapist_data.phone,
                license_number=therapist_data.license_number,
                credentials=therapist_data.credentials,
                specialties=[specialty.value for specialty in therapist_data.specialties],
                years_experience=therapist_data.years_experience,
                bio=therapist_data.bio,
                hourly_rate=therapist_data.hourly_rate,
                accepts_insurance=therapist_data.accepts_insurance,
                insurance_providers=therapist_data.insurance_providers or [],
                availability_schedule={
                    "monday": {"available": False, "hours": []},
                    "tuesday": {"available": False, "hours": []},
                    "wednesday": {"available": False, "hours": []},
                    "thursday": {"available": False, "hours": []},
                    "friday": {"available": False, "hours": []},
                    "saturday": {"available": False, "hours": []},
                    "sunday": {"available": False, "hours": []}
                },  # Default empty schedule
                timezone=therapist_data.timezone,
                is_verified=False,
                is_accepting_new_clients=False  # Until verified
            )
            db.add(therapist_profile)
            db.commit()
            db.refresh(user)

            return user
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error creating therapist: {e}")
            db.rollback()
            raise ValueError("Failed to create therapist account")
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """Deactivate a user account."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = False
                db.commit()
                logger.info(f"Deactivated user: {user.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def activate_user(db: Session, user_id: int) -> bool:
        """Activate a user account."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = True
                db.commit()
                logger.info(f"Activated user: {user.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error activating user: {e}")
            db.rollback()
            return False
