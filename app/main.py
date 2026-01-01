from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import books, reviews, auth, recommendations
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(" Startup: checking DB tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Application runs here

    #  Shutdown logic (optional)
    print("🛑 Shutdown: application stopping")


app = FastAPI(
    title="Intelligent Book Management System",
    lifespan=lifespan
)

# ---------------- ROUTERS ---------------- #

app.include_router(recommendations.router, tags=["Recommendations"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"]) 
app.include_router(books.router, tags=["Books"])
app.include_router(reviews.router, tags=["Reviews"])
