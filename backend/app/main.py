"""FastAPI приложение — точка входа. Подключает роутеры модулей и lifespan."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорт сущностей, чтобы Base.metadata.create_all их увидел.
# В каждом модуле, у которого есть таблицы — импортить entity тут.
from app.generation.domain.models import entity  # noqa: F401  # registers GenerationEntity
from app.generation.client.controller import router as generation_router
from app.shared.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # В проде — Alembic. Тут create_all для простоты демо.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Landing Generator", lifespan=lifespan)

# Vite dev server — другой origin, нужен CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрируем модули
app.include_router(generation_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
