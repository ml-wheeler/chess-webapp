from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 — register models with SQLAlchemy metadata

app = FastAPI(title="Chess API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)


@app.on_event("startup")
def create_database_tables() -> None:
    # Starter setup: create tables automatically. Use Alembic migrations before production.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "chess-api"}
