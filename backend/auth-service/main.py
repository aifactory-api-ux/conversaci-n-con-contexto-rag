import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth_service.config import settings
from backend.auth_service.database import get_db, init_db
from backend.auth_service.dependencies import get_current_user
from backend.auth_service.models.user import UserCreate, UserResponse, TokenData, LoginRequest, TokenResponse
from backend.auth_service.routers import auth_router
from backend.auth_service.services.auth_service import AuthService
from shared.config import settings as shared_settings
from shared.database import db_manager
from shared.exceptions import ApplicationException
from shared.redis_client import RedisClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, shared_settings.LOG_LEVEL),
    format=shared_settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = RedisClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Auth Service...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Connect to Redis
    try:
        await redis_client.connect()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # Don't crash if Redis is unavailable
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth Service...")
    await redis_client.disconnect()
    await db_manager.dispose()
    logger.info("Auth Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and user management service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

# Global exception handler
@app.exception_handler(ApplicationException)
async def application_exception_handler(request, exc: ApplicationException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    # Check database connectivity
    db_healthy = await db_manager.health_check()
    
    # Check Redis connectivity
    redis_healthy = await redis_client.is_connected()
    
    overall_status = "healthy" if db_healthy and redis_healthy else "unhealthy"
    
    return {
        "status": overall_status,
        "service": "auth-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy"
    }

@app.post("/health", include_in_schema=False)
async def health_check_post():
    """Health check endpoint - POST method not allowed."""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed"
    )

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Auth Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
