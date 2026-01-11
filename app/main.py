from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# CRITICAL: Import config first to load .env file before other modules
import app.config

from app.api.routes import books, reviews, auth, recommendations
from app.db.session import engine
from app.db.base import Base

# CRITICAL: Import all ORM models so they're registered in the metadata
# This must happen BEFORE creating tables
from app.models.user import User  # noqa: F401
from app.models.book import Book  # noqa: F401
from app.models.review import Review  # noqa: F401

# Import core modules for production-grade features
from app.core.structured_logging import configure_structured_logging, get_logger
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestResponseMiddleware, ErrorHandlingMiddleware
from app.core.background_tasks import initialize_task_queue, get_task_queue

# Initialize structured logging
configure_structured_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info_with_context("Application startup: checking DB tables")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize background task queue
    task_queue = initialize_task_queue()
    logger.info_with_context("Background task queue initialized")

    yield  # Application runs here

    # Shutdown logic
    logger.info_with_context("Application shutdown: stopping")


app = FastAPI(
    title="Intelligent Book Management System",
    version="2.0.0",
    description="Production-grade book management with AI integration",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE SETUP (Order matters!)
# ============================================================================

# 1. Error handling middleware (outermost)
app.add_middleware(ErrorHandlingMiddleware)

# 2. Request/response logging middleware
app.add_middleware(RequestResponseMiddleware)

# 3. CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Request-ID"],
)

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

register_exception_handlers(app)

# ============================================================================
# ROUTERS
# ============================================================================

app.include_router(recommendations.router, tags=["Recommendations"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"]) 
app.include_router(books.router, tags=["Books"])
app.include_router(reviews.router, tags=["Reviews"])

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    task_queue = get_task_queue()
    stats = await task_queue.get_stats()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "tasks": stats
    }


@app.get("/tasks", tags=["Background Tasks"])
async def list_tasks(
    status: str = None,
    task_type: str = None,
    limit: int = 100
):
    """List background tasks."""
    task_queue = get_task_queue()
    tasks = await task_queue.list_tasks(
        status=status,
        task_type=task_type,
        limit=limit
    )
    return {"tasks": tasks}


@app.get("/tasks/{task_id}", tags=["Background Tasks"])
async def get_task(task_id: str):
    """Get a specific task status."""
    task_queue = get_task_queue()
    try:
        return await task_queue.get_status(task_id)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
