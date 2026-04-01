from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

from shared.config import settings
from shared.database import db_manager
from shared.redis_client import redis_client
from shared.exceptions import ApplicationException
from backend.query_service.router import router as query_router
from backend.query_service.config import get_settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    logger.info("Starting Query Processing Service...")
    
    # Initialize database
    try:
        await db_manager.init_async_engine()
        logger.info("Database engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize Redis
    try:
        await redis_client.connect()
        logger.info("Redis client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise
    
    # Create database tables
    try:
        await db_manager.create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Query Processing Service...")
    await redis_client.disconnect()
    await db_manager.dispose()
    logger.info("Cleanup completed")

# Create FastAPI application
app = FastAPI(
    title="Query Processing Service",
    description="RAG query processing with LangChain/LlamaIndex integration",
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(ApplicationException)
async def application_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "details": str(exc) if settings.DEBUG else None,
        },
    )

# Include routers
app.include_router(query_router, prefix="/api/query", tags=["query"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring."""
    db_healthy = await db_manager.health_check()
    redis_healthy = await redis_client.is_connected()
    
    status = "healthy" if db_healthy and redis_healthy else "unhealthy"
    
    return {
        "status": status,
        "service": "query-service",
        "version": settings.PROJECT_VERSION,
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy",
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Query Processing Service",
        "version": settings.PROJECT_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.QUERY_SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
