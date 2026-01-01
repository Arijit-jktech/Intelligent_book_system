# Intelligent Book Management System

**FastAPI · PostgreSQL · Async SQLAlchemy · JWT · Generative AI · AWS SageMaker**

---

## Project Overview

The **Intelligent Book Management System** is a cloud-ready backend application that allows users to manage books and reviews while leveraging **Generative AI** to create book summaries, review summaries, and recommendations.

The system is built using **FastAPI**, **PostgreSQL**, **asynchronous programming**, and integrates with **AWS SageMaker** for scalable AI inference.  
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

| Layer          | Technology           |
| -------------- | -------------------- |
| API Framework  | FastAPI              |
| Language       | Python 3.11+         |
| Database       | PostgreSQL           |
| ORM            | SQLAlchemy (Async)   |
| Authentication | JWT                  |
| AI Model       | Llama / HuggingFace  |
| ML Platform    | AWS SageMaker        |
| Testing        | Pytest + AsyncIO     |
| Deployment     | Docker (cloud-ready) |

---

## System Architecture

Client (Web / API)
|
v
FastAPI Backend
(Auth, Books, Reviews, RBAC)
|
| HTTPS (JSON)
v
AWS SageMaker Endpoint
(Generative AI Model)
|
v
PostgreSQL Database

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
│ │ └── security.py
│ ├── db/
│ │ ├── base.py
│ │ └── session.py
│ ├── models/
│ ├── schemas/
│ ├── services/
│ │ ├── ai*service.py
│ │ └── sagemaker_client.py
│ └── main.py
│
├── tests/
│ ├── conftest.py
│ └── test*\*.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

## AWS SageMaker Integration

### Why SageMaker?

- Fully managed ML infrastructure
- Auto-scaling inference endpoints
- Secure IAM-based access
- CloudWatch monitoring
- Production-ready AI deployment

### How It Works

- The LLM model is deployed as a **SageMaker real-time endpoint**
- Model artifacts are stored in **Amazon S3**
- FastAPI calls SageMaker using **boto3**
- AI logic is completely decoupled from the backend

### Benefits

- Backend remains lightweight
- AI scales independently
- Easy model upgrades
- No local GPU requirements

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

### Running the Application

1. Create Virtual Environment
   python -m venv venv
   source venv/bin/activate

2. Install Dependencies
   pip install -r requirements.txt

3. Run Server
   uvicorn app.main:app --reload

4. Access API Docs
   Swagger UI: http://localhost:8000/docs
   ReDoc: http://localhost:8000/redoc

### Docker Deploment

docker-compose up --build

### Run Tests

```bash
pytest
```

### Note: AWS SageMaker not be used in this code (Local install) but we can use
