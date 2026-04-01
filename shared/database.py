from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from shared.config import settings


# SQLAlchemy base class for models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self._async_engine: Optional[AsyncEngine] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._sync_engine = None
        self._sync_session_factory = None
    
    def init_async_engine(self) -> None:
        """Initialize async database engine and session factory."""
        if self._async_engine is not None:
            return
        
        db_config = settings.get_database_config()
        
        # Create async engine
        self._async_engine = create_async_engine(
            db_config["url"],
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_timeout=db_config["pool_timeout"],
            pool_recycle=db_config["pool_recycle"],
            echo=db_config["echo"],
            future=True,
        )
        
        # Create async session factory
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    def init_sync_engine(self) -> None:
        """Initialize sync database engine for migrations and tests."""
        if self._sync_engine is not None:
            return
        
        # Convert asyncpg URL to psycopg2 URL for sync operations
        sync_url = str(settings.DATABASE_URL).replace(
            "postgresql+asyncpg", "postgresql+psycopg2"
        )
        
        self._sync_engine = create_engine(
            sync_url,
            pool_size=10,
            max_overflow=5,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )
        
        self._sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if self._async_session_factory is None:
            self.init_async_engine()
        
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """Get a sync database session for migrations."""
        if self._sync_session_factory is None:
            self.init_sync_engine()
        
        session = self._sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @property
    def async_engine(self) -> AsyncEngine:
        """Get the async engine instance."""
        if self._async_engine is None:
            self.init_async_engine()
        return self._async_engine
    
    @property
    def sync_engine(self):
        """Get the sync engine instance."""
        if self._sync_engine is None:
            self.init_sync_engine()
        return self._sync_engine
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.async_engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
    
    async def create_tables(self) -> None:
        """Create all tables defined in models."""
        async with self.async_engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all tables (for testing)."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def dispose(self) -> None:
        """Clean up database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async for session in db_manager.get_async_session():
        yield session


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async for session in db_manager.get_async_session():
        yield session
