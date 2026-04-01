from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from shared.database import get_db
from shared.exceptions import AuthenticationException, ValidationException
from shared.security import password_hasher, token_manager, security_utils

from backend.auth_service.models.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from backend.auth_service.service import AuthService

router = APIRouter()
security = HTTPBearer()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injection for AuthService."""
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Dependency to get current authenticated user."""
    try:
        token = credentials.credentials
        user_id = token_manager.extract_user_id(token)
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise AuthenticationException("User not found")
        return UserResponse.from_orm(user)
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Register a new user."""
    try:
        # Validate email
        if not security_utils.validate_email(user_data.email):
            raise ValidationException("Invalid email format")
        # Validate password strength
        is_valid, errors = security_utils.validate_password_strength(user_data.password)
        if not is_valid:
            raise ValidationException("Password validation failed", field_errors={"password": errors})
        # Check if user already exists
        existing_user = await auth_service._get_user_by_username(user_data.username)
        if existing_user:
            raise ValidationException("Username already exists")
        existing_email = await auth_service._get_user_by_email(user_data.email)
        if existing_email:
            raise ValidationException("Email already registered")
        # Create user
        user = await auth_service.register_user(user_data.username, user_data.email, user_data.password)
        return user
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
            headers={"X-Error-Fields": str(e.field_errors) if hasattr(e, 'field_errors') and e.field_errors else ""},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    try:
        token_response = await auth_service.login_user(login_data.username, login_data.password)
        return token_response
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: dict,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=422, detail="refresh_token is required")
    try:
        access_token = await auth_service.refresh_access_token(refresh_token)
        # For contract, must return {"access_token": ..., "token_type": "bearer"}
        return TokenResponse(access_token=access_token, token_type="bearer", user=None)
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Get current user info."""
    try:
        token = credentials.credentials
        user_id = token_manager.extract_user_id(token)
        user = await auth_service._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            is_active=getattr(user, 'is_active', True)
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
