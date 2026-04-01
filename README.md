# RAG Conversation System

A microservice-based RAG (Retrieval-Augmented Generation) system for conversational interactions with code and documentation.

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Architecture

### System Components

The system consists of 4 backend microservices and 1 frontend:

| Service | Port | Description |
|---------|------|-------------|
| Auth Service | 8001 | User authentication, JWT tokens |
| Query Processing Service | 8002 | RAG query processing with LangChain/LlamaIndex |
| Document Service | 8003 | Document upload, chunking, embedding |
| Conversation Service | 8004 | Conversation and message management |
| Frontend | 3000 | React 18 web interface |
| API Gateway | 8000 | Nginx reverse proxy |

### Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, LangChain
- **Frontend**: React 18, TypeScript, Vite, Zustand
- **Database**: PostgreSQL 15 with pgvector
- **Cache**: Redis 7.2.1
- **Container**: Docker, Docker Compose

### Data Flow

1. User sends query through frontend
2. Query service generates embedding and searches vector DB
3. Relevant document chunks are retrieved
4. LLM generates contextual response using retrieved context
5. Response and sources returned to user

## Prerequisites

- Docker 24.0+
- Docker Compose 2.23+
- 4GB RAM minimum
- 20GB disk space

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd rag-conversation-system
```

### 2. Configure environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set LLM_API_KEY for query service
```

### 3. Start the system

```bash
# On Linux/Mac
./run.sh

# On Windows
run.bat
```

### 4. Access the application

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Auto-generated |
| `POSTGRES_PASSWORD` | PostgreSQL password | postgres |
| `LLM_API_KEY` | OpenAI API key | - |
| `LLM_PROVIDER` | LLM provider (openai/anthropic) | openai |
| `LLM_MODEL` | LLM model name | gpt-3.5-turbo |
| `EMBEDDING_MODEL` | Sentence transformer model | sentence-transformers/all-MiniLM-L6-v2 |
| `REDIS_PASSWORD` | Redis password | - |

### Service Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Auth Service | 8001 | 8001 |
| Query Service | 8002 | 8002 |
| Document Service | 8003 | 8003 |
| Conversation Service | 8004 | 8004 |
| Frontend | 3000 | 3000 |
| API Gateway | 80 | 8000 |

## API Endpoints

### Authentication Service (8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login user |
| POST | /api/auth/refresh | Refresh access token |
| GET | /api/auth/me | Get current user |

### Query Processing Service (8002)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/query | Process RAG query |
| GET | /api/query/history/{conversation_id} | Get query history |

### Document Service (8003)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/documents/upload | Upload document |
| GET | /api/documents | List user documents |
| GET | /api/documents/{document_id} | Get document status |
| DELETE | /api/documents/{document_id} | Delete document |

### Conversation Service (8004)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/conversations | Create conversation |
| GET | /api/conversations | List user conversations |
| GET | /api/conversations/{conversation_id} | Get conversation with messages |
| DELETE | /api/conversations/{conversation_id} | Delete conversation |

### Health Check Endpoints

All services provide health checks at `/health`:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8000/health
```

## Development

### Running with hot reload

For development, you can run services individually:

```bash
# Start infrastructure
docker compose up -d postgres redis

# Start individual services with mounted code
docker compose up auth-service query-service document-service conversation-service

# Start frontend with hot reload
cd frontend && npm run dev
```

### Running tests

```bash
# Backend tests
pytest backend/

# Frontend tests
cd frontend && npm test
```

### Building for production

```bash
# Build all images
docker compose build

# Run production
docker compose up -d
```

## Troubleshooting

### Services not starting

```bash
# Check logs
docker compose logs

# Check specific service
docker compose logs auth-service
```

### Database connection issues

```bash
# Verify postgres is healthy
docker compose ps postgres

# Check postgres logs
docker compose logs postgres
```

### Memory issues

If you encounter out of memory errors:

1. Reduce PostgreSQL memory settings in docker-compose.yml
2. Use smaller embedding model: `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
3. Limit concurrent requests

### LLM API issues

```bash
# Verify LLM_API_KEY is set in .env
cat .env | grep LLM_API_KEY

# Check query service logs
docker compose logs query-service
```

### View all containers

```bash
docker compose ps
```

### Stop all services

```bash
docker compose down
```

### Reset everything

```bash
# Stop and remove all containers, volumes, and images
docker compose down -v --rmi local
```

## License

MIT License

## Support

For issues and questions, please open an issue on the project repository.
