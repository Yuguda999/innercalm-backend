"""
Tests for authentication functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import User
from services.auth_service import AuthService


class TestAuthService:
    """Test AuthService functionality."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = AuthService.get_password_hash(password)
        
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrongpassword", hashed)
    
    def test_create_user(self, db_session: Session, test_user_data: dict):
        """Test user creation."""
        from schemas.user import UserCreate
        user_create = UserCreate(**test_user_data)
        user = AuthService.create_user(db_session, user_create)
        
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.full_name == test_user_data["full_name"]
        assert user.is_active is True
        assert user.hashed_password != test_user_data["password"]
    
    def test_create_duplicate_user(self, db_session: Session, test_user: User, test_user_data: dict):
        """Test creating duplicate user raises error."""
        from schemas.user import UserCreate
        user_create = UserCreate(**test_user_data)
        
        with pytest.raises(ValueError, match="Username already exists"):
            AuthService.create_user(db_session, user_create)
    
    def test_authenticate_user(self, db_session: Session, test_user: User):
        """Test user authentication."""
        # Valid credentials
        authenticated_user = AuthService.authenticate_user(
            db_session, test_user.username, "testpassword123"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        
        # Invalid password
        invalid_user = AuthService.authenticate_user(
            db_session, test_user.username, "wrongpassword"
        )
        assert invalid_user is None
        
        # Invalid username
        invalid_user = AuthService.authenticate_user(
            db_session, "nonexistent", "testpassword123"
        )
        assert invalid_user is None
    
    def test_create_and_verify_token(self, test_user: User):
        """Test JWT token creation and verification."""
        token = AuthService.create_access_token(data={"sub": test_user.username})
        assert token is not None
        
        token_data = AuthService.verify_token(token)
        assert token_data is not None
        assert token_data.username == test_user.username
        
        # Test invalid token
        invalid_token_data = AuthService.verify_token("invalid_token")
        assert invalid_token_data is None


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_user(self, client: TestClient, test_user_data: dict):
        """Test user registration endpoint."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
    
    def test_register_duplicate_user(self, client: TestClient, test_user: User, test_user_data: dict):
        """Test registering duplicate user returns error."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_login_valid_credentials(self, client: TestClient, test_user: User):
        """Test login with valid credentials."""
        response = client.post(
            "/auth/token",
            data={
                "username": test_user.username,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
    
    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/token",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user information."""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert data["is_active"] is True
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test logout endpoint."""
        response = client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]
    
    def test_deactivate_account(self, client: TestClient, auth_headers: dict):
        """Test account deactivation."""
        response = client.post("/auth/deactivate", headers=auth_headers)
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]
        
        # Verify user can't access protected endpoints after deactivation
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 400  # Inactive user
