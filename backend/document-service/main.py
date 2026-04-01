import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.document_service.database.chunk import init_db
from backend.document_service.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    await init_db()
    yield
    # Cleanup on shutdown if needed
    await asyncio.sleep(0)


app = FastAPI(
    title="Document Service",
    description="Service for managing documents and chunks",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
