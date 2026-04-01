from pydantic import BaseModel
from typing import Optional

class DocumentUploadResponse(BaseModel):
    id: str
    status: str
    message: str
    chunks_count: Optional[int] = 0

class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    chunks_count: Optional[int] = 0
    error_message: Optional[str] = None
