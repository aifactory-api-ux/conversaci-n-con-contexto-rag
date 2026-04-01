# DEVELOPMENT PLAN: Conversación con Contexto / RAG

## 1. ARCHITECTURE OVERVIEW

### System Components
This is a microservice-based RAG (Retrieval-Augmented Generation) system for conversational interactions with code and documentation. The architecture consists of:

- **4 Backend Services** (FastAPI, Python 3.11):
  - Auth Service (port 8001): User authentication, JWT tokens
  - Query Processing Service (port 8002): RAG query processing with LangChain/LlamaIndex
  - Document Service (port 8003): Document upload, chunking, embedding
  - Conversation Service (port 8004): Conversation and message management

- **Frontend** (React 18, TypeScript, Vite): Web interface for users

- **Data Layer**:
  - PostgreSQL 15 with pgvector for vector storage
  - Redis for caching
  - SQLAlchemy ORM for data management

### Key Data Models
- User: authentication and user management
- Conversation: conversation threads with title, status
- Message: individual messages within conversations
- Document: uploaded documents with metadata
- Chunk: vector embeddings of document chunks

### API Contracts
Per SPEC.md §3, each service exposes specific REST endpoints with defined request/response schemas.

---

## 2. ACCEPTANCE CRITERIA

1. All 4 backend microservices start successfully and respond to health checks
2. User can register, login, and receive JWT tokens
3. User can upload documents (PDF, DOCX, TXT), which are chunked and vectorized
4. User can create conversations and send messages
5. Query service retrieves relevant document chunks and generates contextual responses using LLM
6. Frontend provides a complete UI for authentication, document management, and chat
7. Redis caching is functional for query responses
8. Complete system runs with `./run.sh` with no manual steps

---

## 3. EXECUTABLE ITEMS

### ITEM 1: Foundation — Shared Types, Config, Database Schemas, Constants
**Goal:** Create all shared code that other items will import. This includes TypeScript interfaces, Python Pydantic/SQLAlchemy models, database schemas, shared utilities, and constants.

**Files to create:**
- shared/types/user.ts (create) - TypeScript User interface, LoginRequest, RegisterRequest, AuthResponse
- shared/types/conversation.ts (create) - TypeScript Conversation, Message interfaces
- shared/types/document.ts (create) - TypeScript Document, DocumentUploadResponse interfaces
- shared/types/query.ts (create) - TypeScript QueryRequest, QueryResponse, SourceChunk interfaces
- shared/config.ts (create) - Environment validation, API configuration constants
- shared/utils.ts (create) - Shared utility functions (formatDate, truncate, etc.)
- shared/models.py (create) - All Pydantic models: UserCreate, UserResponse, TokenData, ConversationCreate, ConversationResponse, MessageCreate, MessageResponse, DocumentUploadResponse, DocumentStatusResponse, QueryRequest, QueryResponse, SourceChunk
- shared/config.py (create) - Environment config loader with pydantic-settings, required env vars validation
- shared/database.py (create) - SQLAlchemy async engine setup, session management
- shared/redis_client.py (create) - Redis async client setup
- shared/security.py (create) - JWT token creation, validation, password hashing
- shared/exceptions.py (create) - Custom exceptions (UnauthorizedException, NotFoundException, etc.)
- shared/constants.py (create) - Application constants (JWT expiration, roles, status values)
- backend/src/db/schema.sql (create) - Complete DB schema with users, conversations, messages, documents, chunks tables + indexes + pgvector extension
- backend/src/db/init.sql (create) - Database initialization script (create extensions, tables)

**Dependencies:** None

**Validation:** All Python files have valid syntax (python -m py_compile), all TypeScript files compile without errors

**Role:** role-tl (technical_lead)

---

### ITEM 2: Auth Service (Port 8001) — Authentication & User Management
**Goal:** Implement authentication service with register, login, token refresh, and user profile endpoints. Uses shared models and database.

**Files to create:**
- backend/auth-service/main.py (create) - FastAPI app entry point with /health endpoint
- backend/auth-service/config.py (create) - Service-specific config (JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)
- backend/auth-service/router.py (create) - API routes: POST /api/auth/register, POST /api/auth/login, POST /api/auth/refresh, GET /api/auth/me
- backend/auth-service/service.py (create) - Business logic: create_user, authenticate_user, create_access_token, get_current_user
- backend/auth-service/models/user.py (create) - Pydantic models specific to auth service
- backend/auth-service/models/token.py (create) - Token response models
- backend/auth-service/database/user.py (create) - SQLAlchemy User model
- backend/auth-service/Dockerfile (create) - Multi-stage build, EXPOSE 8001, CMD: uvicorn src.main:app
- backend/auth-service/requirements.txt (create) - Service-specific dependencies

**Dependencies:** Item 1

**Validation:** Service starts on port 8001, health endpoint returns {status: "healthy", service: "auth-service", version: "1.0.0"}, register/login endpoints respond correctly

**Role:** role-be (backend_developer)

---

### ITEM 3: Query Processing Service (Port 8002) — RAG Query Processing
**Goal:** Implement query service with semantic search, context retrieval, and LLM response generation using LangChain/LlamaIndex.

**Files to create:**
- backend/query-service/main.py (create) - FastAPI app entry point with /health endpoint
- backend/query-service/config.py (create) - Service-specific config (LLM_API_KEY, EMBEDDING_MODEL, TOP_K_CHUNKS)
- backend/query-service/router.py (create) - API routes: POST /api/query, GET /api/query/history/{conversation_id}
- backend/query-service/service.py (create) - Main query processing logic
- backend/query-service/models/query.py (create) - QueryRequest Pydantic model
- backend/query-service/models/response.py (create) - QueryResponse Pydantic model
- backend/query-service/services/embedding.py (create) - Query embedding generation using sentence-transformers
- backend/query-service/services/vector_search.py (create) - Vector similarity search using pgvector
- backend/query-service/services/llm_generator.py (create) - LLM response generation using LangChain
- backend/query-service/services/cache.py (create) - Redis caching for query responses
- backend/query-service/Dockerfile (create) - Multi-stage build, EXPOSE 8002, CMD: uvicorn src.main:app
- backend/query-service/requirements.txt (create) - Service-specific dependencies

**Dependencies:** Item 1

**Validation:** Service starts on port 8002, health endpoint responds, query endpoint processes requests and returns responses with sources

**Role:** role-be (backend_developer)

---

### ITEM 4: Document Service (Port 8003) — Document Upload & Processing
**Goal:** Implement document service for uploading files, extracting content, chunking, and generating embeddings.

**Files to create:**
- backend/document-service/main.py (create) - FastAPI app entry point with /health endpoint
- backend/document-service/config.py (create) - Service-specific config (UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP)
- backend/document-service/router.py (create) - API routes: POST /api/documents/upload, GET /api/documents, GET /api/documents/{document_id}, DELETE /api/documents/{document_id}
- backend/document-service/service.py (create) - Document processing orchestration
- backend/document-service/processors/pdf_processor.py (create) - PDF text extraction using PyPDF2
- backend/document-service/processors/docx_processor.py (create) - DOCX text extraction using python-docx
- backend/document-service/processors/txt_processor.py (create) - Plain text file processing
- backend/document-service/processors/chunker.py (create) - Text chunking logic
- backend/document-service/processors/embedder.py (create) - Embedding generation for chunks
- backend/document-service/database/document.py (create) - SQLAlchemy Document model
- backend/document-service/database/chunk.py (create) - SQLAlchemy Chunk model with vector field
- backend/document-service/Dockerfile (create) - Multi-stage build, EXPOSE 8003, CMD: uvicorn src.main:app
- backend/document-service/requirements.txt (create) - Service-specific dependencies

**Dependencies:** Item 1

**Validation:** Service starts on port 8003, health endpoint responds, file upload creates document and processes chunks

**Role:** role-be (backend_developer)

---

### ITEM 5: Conversation Service (Port 8004) — Conversation & Message Management
**Goal:** Implement conversation service for creating conversations, managing messages, and retrieving conversation history.

**Files to create:**
- backend/conversation-service/main.py (create) - FastAPI app entry point with /health endpoint
- backend/conversation-service/config.py (create) - Service-specific config
- backend/conversation-service/router.py (create) - API routes: POST /api/conversations, GET /api/conversations, GET /api/conversations/{conversation_id}, DELETE /api/conversations/{conversation_id}
- backend/conversation-service/service.py (create) - Business logic for conversations and messages
- backend/conversation-service/database/conversation.py (create) - SQLAlchemy Conversation model
- backend/conversation-service/database/message.py (create) - SQLAlchemy Message model
- backend/conversation-service/Dockerfile (create) - Multi-stage build, EXPOSE 8004, CMD: uvicorn src.main:app
- backend/conversation-service/requirements.txt (create) - Service-specific dependencies

**Dependencies:** Item 1

**Validation:** Service starts on port 8004, health endpoint responds, CRUD operations for conversations work correctly

**Role:** role-be (backend_developer)

---

### ITEM 6: Frontend — React 18 Web Application
**Goal:** Build complete React frontend for authentication, document management, and chat interface. Uses shared types from Item 1.

**Files to create:**
- frontend/src/main.tsx (create) - React app entry point
- frontend/src/App.tsx (create) - Main App component with routing
- frontend/src/App.css (create) - Global styles
- frontend/src/index.css (create) - Tailwind CSS imports
- frontend/src/api/auth.ts (create) - Axios client for auth endpoints
- frontend/src/api/documents.ts (create) - Axios client for document endpoints
- frontend/src/api/conversations.ts (create) - Axios client for conversation endpoints
- frontend/src/api/query.ts (create) - Axios client for query endpoints
- frontend/src/hooks/useAuth.ts (create) - Auth state management with Zustand
- frontend/src/hooks/useChat.ts (create) - Chat state management with Zustand
- frontend/src/components/Layout.tsx (create) - Main layout component
- frontend/src/components/Header.tsx (create) - Header with navigation
- frontend/src/components/LoginForm.tsx (create) - Login form component
- frontend/src/components/RegisterForm.tsx (create) - Registration form component
- frontend/src/components/DocumentList.tsx (create) - Document list component
- frontend/src/components/DocumentUpload.tsx (create) - File upload component
- frontend/src/components/ChatWindow.tsx (create) - Chat interface component
- frontend/src/components/MessageBubble.tsx (create) - Message display component
- frontend/src/components/SourceCitations.tsx (create) - Source chunk display component
- frontend/src/pages/LoginPage.tsx (create) - Login page
- frontend/src/pages/RegisterPage.tsx (create) - Registration page
- frontend/src/pages/DashboardPage.tsx (create) - Main dashboard with documents and chat
- frontend/src/pages/ChatPage.tsx (create) - Chat page
- frontend/vite.config.ts (create) - Vite configuration
- frontend/tsconfig.json (create) - TypeScript configuration
- frontend/tailwind.config.js (create) - Tailwind CSS configuration
- frontend/postcss.config.js (create) - PostCSS configuration
- frontend/index.html (create) - HTML entry point
- frontend/Dockerfile (create) - Multi-stage build with nginx, EXPOSE 80
- frontend/package.json (create) - Dependencies including react-router-dom, axios, zustand, lucide-react

**Dependencies:** Item 1

**Validation:** Frontend builds without errors, starts and displays UI correctly

**Role:** role-fe (frontend_developer)

---

### ITEM 7: Infrastructure & Deployment — Docker Orchestration
**Goal:** Complete Docker orchestration with all services, health checks, and zero manual setup. Creates run.sh, docker-compose.yml, environment files.

**Files to create:**
- docker-compose.yml (create) - All services with healthchecks, depends_on with service_healthy, PostgreSQL 15 + pgvector, Redis 7
- .env.example (create) - All environment variables with descriptions: JWT_SECRET, DATABASE_URL, REDIS_URL, LLM_API_KEY, etc.
- .gitignore (create) - Exclude node_modules, dist, .env, __pycache__, *.pyc
- .dockerignore (create) - Exclude node_modules, .git, *.log, dist
- run.sh (create) - Validates Docker, builds services, starts containers, waits for healthy, prints access URL
- run.bat (create) - Windows equivalent batch script
- README.md (create) - Complete documentation: Prerequisites | Clone | Run | Test | Endpoints
- docs/architecture.md (create) - System diagram and component descriptions

**Dependencies:** All previous items (Items 1-6)

**Validation:** './run.sh' completes without errors, all services report healthy, frontend accessible at localhost, all API endpoints respond correctly

**Role:** role-devops (devops_support)