import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from shared.config import settings
from shared.exceptions import AuthenticationException


class PasswordHasher:
    """Handles password hashing and verification."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storage."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """Handles JWT token creation and validation."""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                raise AuthenticationException(f"Invalid token type: expected {token_type}")
            
            return payload
        except JWTError as e:
            raise AuthenticationException(f"Invalid token: {str(e)}")
    
    def extract_user_id(self, token: str) -> str:
        """Extract user ID from a valid access token."""
        payload = self.verify_token(token, "access")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException("Token does not contain user ID")
        return user_id


class SecurityUtils:
    """General security utilities."""
    
    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """Generate a cryptographically secure random string."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """Validate password strength."""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not input_string:
            return ""
        
        # Trim whitespace
        sanitized = input_string.strip()
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_patterns = [
            ("<script>", ""),
            ("</script>", ""),
            ("javascript:", ""),
            ("onload=", ""),
            ("onerror=", ""),
            ("onclick=", ""),
            ("<", "&lt;"),
            (">", "&gt;"),
            ("'", "&#39;"),
            ('"', "&quot;"),
        ]
        
        for pattern, replacement in dangerous_patterns:
            sanitized = sanitized.replace(pattern, replacement)
        
        return sanitized


# Global instances
password_hasher = PasswordHasher()
token_manager = TokenManager()
security_utils = SecurityUtils()