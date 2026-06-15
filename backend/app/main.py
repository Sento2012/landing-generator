"""FastAPI приложение — точка входа. Подключает роутеры модулей и lifespan."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.generation.client.controller import router as generation_router
from app.shared.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Схема БД — через Alembic (см. сервис `migrate` в docker-compose.yml).
    # Тут только cleanup на остановке.
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
