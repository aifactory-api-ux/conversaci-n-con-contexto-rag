# SPEC.md

## 1. TECHNOLOGY STACK

### Backend
- **Runtime**: Python 3.11.9 (exact version in Dockerfile)
- **Web Framework**: FastAPI 0.109.0
- **ORM**: SQLAlchemy 2.0.25
- **Database Driver**: asyncpg 0.29.0
- **Vector Database**: PostgreSQL 15.4 with pgvector 0.2.0 extension
- **Caching**: Redis 7.2.1 (via redis-py async 5.0.1)
- **LLM Integration**: LangChain 0.1.6, LangChain-community 0.1.6
- **Embedding**: sentence-transformers 2.2.2, LlamaIndex 0.9.46
- **Authentication**: python-jose[cryptography] 3.3.0, passlib[bcrypt] 1.7.4
- **Validation**: Pydantic 2.5.3, pydantic-settings 2.1.0
- **Document Processing**: PyPDF2 3.0.1, python-docx 1.1.0
- **Server**: uvicorn[standard] 0.27.0

### Frontend
- **Runtime**: Node.js 20.11.0 (exact version)
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.3.3
- **Build Tool**: Vite 5.0.12
- **Routing**: react-router-dom 6.21.3
- **HTTP Client**: axios 1.6.7
- **State Management**: Zustand 4.5.0
- **UI Components**: Custom components with Tailwind CSS 3.4.1
- **Icons**: lucide-react 0.312.0

### Infrastructure
- **Container Runtime**: Docker 24.0.7
- **Container Orchestration**: Kubernetes 1.28.5
- **Image Builder**: docker-compose 2.23.3

---

## 2. DATA CONTRACTS

### Backend Pydantic Models

```python
# backend/models/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserResponse(UserBase):
    id: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
```

```python
# backend/models/conversation.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    
class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    started_at: datetime
    last_activity: datetime
    status: str
    
    class Config:
        from_attributes = True
```

```python
# backend/models/message.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(..., pattern="^(user|assistant)$")

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[str] = None
    
    class Config:
        from_attributes = True
```

```python
# backend/models/document.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DocumentUploadResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    content_type: str
    uploaded_at: datetime
    status: str
    
    class Config:
        from_attributes = True

class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    chunks_count: Optional[int] = None
    error_message: Optional[str] = None
```

```python
# backend/models/query.py
from pydantic import BaseModel, Field
from typing import Optional, List

class QueryRequest(BaseModel):
    conversation_id: str
    message: str = Field(..., min_length=1, max_length=5000)
    include_sources: bool = True

class SourceChunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    document_filename: str

class QueryResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    sources: Optional[List[SourceChunk]] = None
    cached: bool = False
```

### Frontend TypeScript Interfaces

```typescript
// src/types/user.ts
export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
```

```typescript
// src/types/conversation.ts
export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  started_at: string;
  last_activity: string;
  status: 'active' | 'archived';
}

export interface ConversationCreate {
  title: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: string;
}
```

```typescript
// src/types/document.ts
export interface Document {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunks_count?: number;
}

export interface DocumentUploadResponse {
  id: string;
  status: string;
  message: string;
}
```

```typescript
// src/types/query.ts
export interface QueryRequest {
  conversation_id: string;
  message: string;
  include_sources: boolean;
}

export interface SourceChunk {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  document_filename: string;
}

export interface QueryResponse {
  response: string;
  conversation_id: string;
  message_id: string;
  sources?: SourceChunk[];
  cached: boolean;
}
```

---

## 3. API ENDPOINTS

### Authentication Service (port 8001)

| Method | Path | Request Body | Response |
|--------|------|--------------|----------|
| POST | /api/auth/register | {"username": "string", "email": "string", "password": "string"} | {"id": "string", "username": "string", "email": "string", "created_at": "datetime", "is_active": true} |
| POST | /api/auth/login | {"username": "string", "password": "string"} | {"access_token": "string", "token_type": "bearer", "user": {...}} |
| POST | /api/auth/refresh | {"refresh_token": "string"} | {"access_token": "string", "token_type": "bearer"} |
| GET | /api/auth/me | (Bearer Token) | {"id": "string", "username": "string", "email": "string", ...} |

### Query Processing Service (port 8002)

| Method | Path | Request Body | Response |
|--------|------|--------------|----------|
| POST | /api/query | {"conversation_id": "string", "message": "string", "include_sources": true} | {"response": "string", "conversation_id": "string", "message_id": "string", "sources": [...], "cached": false} |
| GET | /api/query/history/{conversation_id} | (Bearer Token) | {"messages": [...]} |

### Document Service (port 8003)

| Method | Path | Request Body | Response |
|--------|------|--------------|----------|
| POST | /api/documents/upload | multipart/form-data (file) | {"id": "string", "status": "pending", "message": "string"} |
| GET | /api/documents | (Bearer Token) | {"documents": [...]} |
| GET | /api/documents/{document_id} | (Bearer Token) | {"id": "string", "status": "completed", "chunks_count": 10} |
| DELETE | /api/documents/{document_id} | (Bearer Token) | {"message": "Document deleted successfully"} |

### Conversation Service (port 8004)

| Method | Path | Request Body | Response |
|--------|------|--------------|----------|
| POST | /api/conversations | {"title": "string"} | {"id": "string", "user_id": "string", "title": "string", ...} |
| GET | /api/conversations | (Bearer Token) | {"conversations": [...]} |
| GET | /api/conversations/{conversation_id} | (Bearer Token) | {"id": "string", "messages": [...]} |
| DELETE | /api/conversations/{conversation_id} | (Bearer Token) | {"message": "Conversation deleted successfully"} |

### Health Check Endpoints

| Method | Path | Response |
|--------|------|----------|
| GET | /health | {"status": "healthy", "service": "auth-service", "version": "1.0.0"} |
| GET | /health | {"status": "healthy", "service": "query-service", "version": "1.0.0"} |
| GET | /health | {"status": "healthy", "service": "document-service", "version": "1.0.0"} |
| GET | /health | {"status": "healthy", "service": "conversation-service", "version": "1.0.0"} |

---

## 4. FILE STRUCTURE

```
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── run.sh
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   │
│   ├── shared/                           # Shared modules across services
│   │   ├── __init__.py
│   │   ├── config.py                     # Environment config loader
│   │   ├── database.py                   # SQLAlchemy async engine
│   │   ├── redis_client.py               # Redis async client
│   │   ├── security.py                   # JWT token creation/validation
│   │   ├── exceptions.py                 # Custom exceptions
│   │   └── constants.py                  # App constants
│   │
│   ├── auth-service/                     # Port 8001
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI app entry point
│   │   ├── config.py                     # Service-specific config
│   │   ├── router.py                     # API routes
│   │   ├── service.py                    # Business logic
│   │   ├── models/                       # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── token.py
│   │   └── database/                     # SQLAlchemy models
│   │       ├── __init__.py
│   │       └── user.py
│   │
│   ├── query-service/                    # Port 8002
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── router.py
│   │   ├── service.py                    # Query processing logic
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── query.py
│   │   │   └── response.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── embedding.py              # Query embedding generation
│   │   │   ├── vector_search.py          # Semantic search
│   │   │   ├── llm_generator.py         # LLM response generation
│   │   │   └── cache.py                 # Redis caching
│   │   └── database/
│   │       ├── __init__.py
│   │       ├── message.py
│   │       └── chunk.py
│   │
│   ├── document-service/                 # Port 8003
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── document.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── processor.py             # File parsing
│   │   │   ├── chunker.py               # Text chunking
│   │   │   └── indexer.py               # Vector indexing
│   │   └── database/
│   │       ├── __init__.py
│   │       └── document.py
│   │
│   └── conversation-service/             # Port 8004
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── router.py
│       ├── service.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── conversation.py
│       └── database/
│           ├── __init__.py
│           └── conversation.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    ├── .env.example
    │
    ├── src/
    │   ├── main.tsx                       # React entry point
    │   ├── App.tsx                        # Root component
    │   ├── index.css                      # Global styles
    │
    │   ├── types/                         # TypeScript interfaces
    │   │   ├── index.ts
    │   │   ├── user.ts
    │   │   ├── conversation.ts
    │   │   ├── document.ts
    │   │   └── query.ts
    │
    │   ├── api/                           # API client layer
    │   │   ├── index.ts
    │   │   ├── auth.ts
    │   │   ├── conversations.ts
    │   │   ├── documents.ts
    │   │   └── query.ts
    │
    │   ├── stores/                        # Zustand stores
    │   │   ├── index.ts
    │   │   ├── authStore.ts
    │   │   ├── conversationStore.ts
    │   │   ├── documentStore.ts
    │   │   └── queryStore.ts
    │
    │   ├── hooks/                         # React hooks
    │   │   ├── useAuth.ts
    │   │   ├── useConversations.ts
    │   │   ├── useDocuments.ts
    │   │   └── useQuery.ts
    │
    │   ├── components/                    # Reusable components
    │   │   ├── layout/
    │   │   │   ├── Header.tsx
    │   │   │   ├── Sidebar.tsx
    │   │   │   └── Layout.tsx
    │   │   ├── auth/
    │   │   │   ├── LoginForm.tsx
    │   │   │   ├── RegisterForm.tsx
    │   │   │   └── ProtectedRoute.tsx
    │   │   ├── chat/
    │   │   │   ├── ChatWindow.tsx
    │   │   │   ├── MessageList.tsx
    │   │   │   ├── MessageBubble.tsx
    │   │   │   ├── ChatInput.tsx
    │   │   │   └── SourceCards.tsx
    │   │   ├── documents/
    │   │   │   ├── DocumentList.tsx
    │   │   │   ├── DocumentCard.tsx
    │   │   │   ├── DocumentUploader.tsx
    │   │   │   └── DocumentStatus.tsx
    │   │   └── common/
    │   │       ├── Button.tsx
    │   │       ├── Input.tsx
    │   │       ├── Spinner.tsx
    │   │       └── ErrorMessage.tsx
    │
    │   ├── pages/                         # Page components
    │   │   ├── index.tsx
    │   │   ├── Login.tsx
    │   │   ├── Register.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── Chat.tsx
    │   │   ├── Documents.tsx
    │   │   └── Settings.tsx
    │
    │   └── utils/                         # Utility functions
    │       ├── formatDate.ts
    │       ├── storage.ts
    │       └── validation.ts
    │
    └── public/
        └── favicon.ico
```

### PORT TABLE

| Service | Listening Port | Path |
|---------|-----------------|------|
| auth-service | 8001 | backend/auth-service/ |
| query-service | 8002 | backend/query-service/ |
| document-service | 8003 | backend/document-service/ |
| conversation-service | 8004 | backend/conversation-service/ |
| frontend | 3000 | frontend/ |

### SHARED MODULES

| Shared path | Imported by services |
|------------|---------------------|
| backend/shared/ | auth-service, query-service, document-service, conversation-service |

---

## 5. ENVIRONMENT VARIABLES

### Backend Shared Configuration (backend/shared/config.py loads these)

| Name | Type | Description | Example Value |
|------|------|-------------|---------------|
| DATABASE_URL | string | PostgreSQL connection string with pgvector | postgresql+asyncpg://user:pass@postgres:5432/ragdb |
| REDIS_URL | string | Redis connection string | redis://redis:6379/0 |
| JWT_SECRET_KEY | string | Secret key for JWT signing | your-super-secret-key-change-in-production |
| JWT_ALGORITHM | string | Algorithm for JWT | HS256 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | int | Access token expiration | 30 |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | int | Refresh token expiration | 7 |

### Auth Service Specific

| Name | Type | Description | Example Value |
|------|------|-------------|---------------|
| AUTH_SERVICE_HOST | string | Service host | 0.0.0.0 |
| AUTH_SERVICE_PORT | int | Service port | 8001 |
| CORS_ORIGINS | string | Allowed origins | http://localhost:3000 |

### Query Service Specific

| Name | Type | Description | Example Value |
|------|------|-------------|---------------|
| QUERY_SERVICE_HOST | string | Service host | 0.0.0.0 |
| QUERY_SERVICE_PORT | int | Service port | 8002 |
| EMBEDDING_MODEL | string | Sentence transformer model | sentence-transformers/all-MiniLM-L6-v2 |
| LLM_PROVIDER | string | LLM provider (openai/anthropic/local) | openai |
| LLM_API_KEY | string | API key for external LLM | sk-... |
| LLM_MODEL_NAME | string | Model name | gpt-4 |
| LLM_TEMPERATURE | float | Generation temperature | 0.7 |
| TOP_K_CHUNKS | int | Number of chunks to retrieve | 5 |
| SIMILARITY_THRESHOLD | float | Minimum similarity score | 0.7 |

### Document Service Specific

| Name | Type | Description | Example Value |
|------|------|-------------|---------------|
| DOCUMENT_SERVICE_HOST | string | Service host | 0.0.0.0 |
| DOCUMENT_SERVICE_PORT | int | Service port | 8003 |
| UPLOAD_DIR | string | File upload directory | /tmp/uploads |
| MAX_FILE_SIZE_MB | int | Maximum upload size | 50 |
| ALLOWED_EXTENSIONS | string | Allowed file types | .pdf,.docx,.txt,.md |
| CHUNK_SIZE | int | Text chunk size in characters | 1000 |
| CHUNK_OVERLAP | int | Overlap between chunks | 200 |

### Conversation Service Specific

| Name | Type | Description | Example Value |
|------|------|-------------|---------------|
| CONVERSATION_SERVICE_HOST | string | Service host | 0.0.0.0 |
| CONVERSATION_SERVICE_PORT | int | Service port | 8004 |

### Frontend Configuration

| Name | Type | Description | Example Value |
|------|------|-------------|---------------|
| VITE_API_URL | string | Backend API base URL | http://localhost:8001 |
| VITE_WS_URL | string | WebSocket URL | ws://localhost:8002/ws |

---

## 6. IMPORT CONTRACTS

### Backend Shared Module Exports (backend/shared/)

```python
# backend/shared/config.py
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

settings: Settings = Settings()
```

```python
# backend/shared/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

async def get_db() -> AsyncSession:
    """Yield database session"""
    
async def init_db():
    """Initialize database tables"""
```

```python
# backend/shared/redis_client.py
from redis.asyncio import Redis

redis_client: Redis = None

async def get_redis() -> Redis:
    """Get Redis client"""
    
async def close_redis():
    """Close Redis connection"""
```

```python
# backend/shared/security.py
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool
def get_password_hash(password: str) -> str
def create_access_token(data: dict, expires_delta: timedelta) -> str
def create_refresh_token(data: dict, expires_delta: timedelta) -> str
def decode_token(token: str) -> dict
async def get_current_user(token: str) -> User
```

```python
# backend/shared/exceptions.py
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400)

class NotFoundException(AppException)
class UnauthorizedException(AppException)
class ValidationException(AppException)
```

```python
# backend/shared/constants.py
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

### Backend Service Imports

```python
# auth-service imports
from shared.config import settings
from shared.database import Base, get_db, init_db
from shared.redis_client import get_redis, close_redis
from shared.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from shared.exceptions import NotFoundException, UnauthorizedException
from shared.constants import CHUNK_SIZE
from .models.user import UserCreate, UserResponse, TokenData
from .database.user import User
```

```python
# query-service imports
from shared.config import settings
from shared.database import Base, get_db
from shared.redis_client import get_redis
from shared.security import get_current_user
from .services.embedding import EmbeddingService
from .services.vector_search import VectorSearchService
from .services.llm_generator import LLMGeneratorService
from .services.cache import CacheService
```

### Frontend Exports

```typescript
// src/api/index.ts
export const apiClient: AxiosInstance
export const setAuthToken: (token: string) => void
export const clearAuthToken: () => void
```

```typescript
// src/stores/authStore.ts
export const useAuthStore: () => {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}
```

```typescript
// src/stores/conversationStore.ts
export const useConversationStore: () => {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  error: string | null;
  fetchConversations: () => Promise<void>;
  createConversation: (title: string) => Promise<Conversation>;
  selectConversation: (id: string) => Promise<void>;
  deleteConversation: (