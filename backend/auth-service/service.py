import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth_service.database.user import User, UserStatus
from backend.auth_service.models.user import UserResponse, TokenResponse
from shared.exceptions import AuthenticationException, ValidationException, NotFoundException
from shared.security import password_hasher, token_manager


class AuthService:
    """Service layer for authentication and user management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, username: str, email: str, password: str) -> UserResponse:
        """Register a new user."""
        # Validate input
        if len(username) < 3 or len(username) > 50:
            raise ValidationException("Username must be between 3 and 50 characters")
        
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        # Check if user already exists
        existing_user = await self._get_user_by_username(username)
        if existing_user:
            raise ValidationException("Username already exists")
        
        existing_email = await self._get_user_by_email(email)
        if existing_email:
            raise ValidationException("Email already registered")
        
        # Hash password
        hashed_password = password_hasher.hash_password(password)
        
        # Create user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.status == UserStatus.ACTIVE
        )
    
    async def login_user(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and return tokens."""
        # Get user
        user = await self._get_user_by_username(username)
        if not user:
            raise AuthenticationException("Invalid username or password")
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("User account is not active")
        
        # Verify password
        if not password_hasher.verify_password(password, user.hashed_password):
            raise AuthenticationException("Invalid username or password")
        
        # Create tokens
        token_data = {"sub": user.id, "username": user.username}
        access_token = token_manager.create_access_token(token_data)
        refresh_token = token_manager.create_refresh_token(token_data)
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        # Prepare user response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.status == UserStatus.ACTIVE
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user=user_response
        )
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = token_manager.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationException("Invalid refresh token")
            
            # Get user
            user = await self._get_user_by_id(user_id)
            if not user or user.status != UserStatus.ACTIVE:
                raise AuthenticationException("User not found or inactive")
            
            # Create new access token
            token_data = {"sub": user.id, "username": user.username}
            new_access_token = token_manager.create_access_token(token_data)
            
            return new_access_token
            
        except AuthenticationException:
            raise
        except Exception as e:
            raise AuthenticationException(f"Token refresh failed: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        user = await self._get_user_by_id(user_id)
        if not user:
            return None
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.status == UserStatus.ACTIVE
        )
    
    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()