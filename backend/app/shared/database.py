"""Async SQLAlchemy 2.0 + asyncpg. Общая инфраструктура для всех модулей."""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://landing:landing@localhost:5432/landing",
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей разных модулей."""
    pass


async def get_session() -> AsyncSession:
    """FastAPI dependency: сессия на запрос."""
    async with SessionLocal() as session:
        yield session
