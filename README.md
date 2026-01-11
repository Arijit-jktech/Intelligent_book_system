# Intelligent Book Management System

**FastAPI · PostgreSQL · Async SQLAlchemy · JWT · Generative AI · Ollama**

---

## Project Overview

The **Intelligent Book Management System** is a cloud-ready backend application that allows users to manage books and reviews while leveraging **Generative AI** to create book summaries, review summaries, and recommendations.

The system is built using **FastAPI**, **PostgreSQL**, **asynchronous programming**, and integrates with **Ollama** for local or self-hosted LLM inference.  
It follows **enterprise-level architecture, security, and testing best practices**.

---

## Key Features

### 📘 Book Management

- Add, update, retrieve, and delete books
- Store metadata: title, author, genre, year published
- Auto-generate AI-powered book summaries

### Reviews & Ratings

- Users can add reviews and ratings
- View all reviews for a book
- Generate AI-based review summaries
- Calculate average book ratings

### 🤖 Generative AI

- AI-generated book summaries
- AI-generated review summaries
- AI-based book recommendations
- AI deployed using **AWS SageMaker** (cloud-ready)

### Authentication & Security

- JWT-based authentication
- Role-based access control (**Admin / User**)
- Secure API endpoints
- IAM-based access for cloud services

### Engineering Best Practices

- Fully asynchronous backend
- Modular and testable codebase
- Clean separation of concerns
- Mocked AI calls in tests
- Swagger / OpenAPI documentation

---

## Tech Stack

| Layer            | Technology                      |
| ---------------- | ------------------------------- |
| API Framework    | FastAPI                         |
| Language         | Python 3.11+                    |
| Database         | PostgreSQL + SQLite (dev)       |
| ORM              | SQLAlchemy (Async)              |
| Authentication   | JWT + OAuth2PasswordBearer      |
| Password Hashing | Argon2 / Bcrypt                 |
| AI Model         | Ollama (Llama 3 or HuggingFace) |
| AI Inference     | Local Ollama or Remote          |
| Caching          | Redis                           |
| Testing          | Pytest + AsyncIO                |
| Deployment       | Docker + Docker Compose         |

---

## System Architecture

```
Client (Web / API)
    |
    v
FastAPI Backend
(Auth, Books, Reviews, Recommendations, RBAC)
    |
    +----> PostgreSQL Database (persistence)
    |
    +----> Redis Cache (recommendations, caching)
    |
    +----> Ollama LLM Service (AI summaries)
            (local or remote)
```

---

## Project Structure

intelligent-book-management-system/
│
├── app/
│ ├── api/
│ │ └── routes/
│ │ ├── auth.py
│ │ ├── books.py
│ │ ├── reviews.py
│ │ └── recommendations.py
│ ├── core/
│ │ ├── security.py
│ │ └── cache.py
│ ├── db/
│ │ ├── base.py
│ │ └── session.py
│ ├── models/
│ │ ├── user.py
│ │ ├── book.py
│ │ └── review.py
│ ├── schemas/
│ │ ├── auth.py
│ │ ├── book.py
│ │ └── review.py
│ ├── services/
│ │ ├── ai*service.py
│ │ ├── summary_service.py
│ │ ├── recommendation_service.py
│ │ └── recommendation_cache.py
│ ├── config.py
│ └── main.py
│
├── tests/
│ ├── conftest.py
│ ├── db_test.py
│ └── test*\*.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md

---

## Ollama AI Integration

### Why Ollama?

- **Local AI inference**: No cloud dependencies or API costs
- **Privacy**: All data stays on your infrastructure
- **Flexible models**: Supports Llama 3, Mistral, and other open models
- **Development-friendly**: Easy to set up and test locally
- **Production-ready**: Can be deployed on-premise or cloud VMs
- **Resilient**: Built-in retry logic with exponential backoff

### How It Works

- Ollama runs as a local service (or remote endpoint)
- FastAPI calls Ollama REST API with book/review prompts
- LLM generates summaries asynchronously
- Results are cached in Redis for performance
- If Ollama is unavailable, fallback summaries are generated from metadata

### Configuration

All Ollama settings are externalized via environment variables:

```bash
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3:8b
OLLAMA_TIMEOUT=120          # seconds
OLLAMA_RETRIES=3            # retry attempts
OLLAMA_BACKOFF=1            # exponential backoff multiplier (seconds)
```

### Installation & Setup

**Option 1: Local Ollama (Recommended for Development)**

```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3:8b

# Ollama listens on http://localhost:11434 by default
```

**Option 2: Remote Ollama Server**

```bash
# Set OLLAMA_URL to your remote server:
export OLLAMA_URL=http://your-server:11434/api/generate
```

### Error Handling

- Automatic retries with exponential backoff
- Connection timeouts after 120 seconds (configurable)
- Graceful fallback to metadata-based summaries if AI unavailable
- Detailed logging for debugging

---

## Authentication & Authorization

### Roles

**Admin**

- Manage books
- Generate summaries

**User**

- View books
- Add reviews

### Security

- JWT-based authentication
- Role-based access control
- Secure token validation
- No credentials stored in code

---

## API Endpoints

### Auth

- `POST /auth/signup`
- `POST /auth/login`

### Books

- `POST /books`
- `GET /books`
- `GET /books/{id}`
- `PUT /books/{id}`
- `DELETE /books/{id}`

### Reviews

- `POST /books/{id}/reviews`
- `GET /books/{id}/reviews`
- `GET /books/{id}/reviews_summary`

### AI

- `POST /generate-summary`
- `GET /books/{id}/summary`
- `GET /recommendations`

---

## Testing

### Test Coverage

- Authentication
- RBAC rules
- Books CRUD
- Reviews & summaries
- AI endpoints (mocked)

### Testing Approach

- Async pytest
- Isolated SQLite test database
- AI calls fully mocked
- No cloud dependency during tests

## Running the Application

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use SQLite for development)
- Ollama (for AI features)
- Redis (for caching)

### Local Development Setup

**1. Clone and Setup Environment**

```bash
git clone <repo>
cd intelligent-book-management-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**2. Configure Environment**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# CRITICAL: Set a strong SECRET_KEY in production
nano .env
```

**3. Start Ollama (in another terminal)**

```bash
# Pull Ollama if not already installed
ollama pull llama3:8b

# Start Ollama service
ollama serve
# Ollama listens on http://localhost:11434
```

**4. Start PostgreSQL or use SQLite**

For SQLite (development):

```bash
# Already configured in .env as:
# DATABASE_URL=sqlite+aiosqlite:///:memory:
```

For PostgreSQL:

```bash
# Start PostgreSQL, then update .env:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/books_db
```

**5. Run the Application**

```bash
uvicorn app.main:app --reload
```

Access the API:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Docker Deployment

**Quick Start with Docker Compose**

```bash
# Copy and configure environment
cp .env.example .env
nano .env  # Set SECRET_KEY and other production values

# Build and start all services
docker-compose up --build

# Access API at http://localhost:8000/docs
```

**What docker-compose starts:**

- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI (port 8000)
- Note: Ollama must run separately (see: https://hub.docker.com/r/ollama/ollama)

**Running Ollama in Docker**

```bash
# In another terminal, start Ollama container
docker run -d -p 11434:11434 ollama/ollama:latest
docker exec <container-id> ollama pull llama3:8b
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_auth_signup.py -v

# With coverage
pytest --cov=app tests/
```

---

## Security Best Practices

### Environment Configuration

1. **Never commit `.env` file** — it contains secrets

   - ✓ `.env.example` is committed (template only)
   - ✗ `.env` is in `.gitignore` (secrets)

2. **Generate strong SECRET_KEY** for production:

   ```bash
   openssl rand -hex 32
   ```

3. **All credentials are externalized**:

   - Database credentials
   - JWT secret
   - API endpoints
   - Timeout/retry settings

4. **Authentication**:
   - Passwords hashed with Argon2/Bcrypt (72-byte limit enforced)
   - JWT tokens with configurable expiration
   - Role-based access control (Admin/User)
   - OAuth2PasswordBearer with Swagger integration
