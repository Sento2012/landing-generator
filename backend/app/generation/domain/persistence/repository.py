"""Repository — операции ЧТЕНИЯ генераций.

Два набора методов:
- `find_by_id` — без фильтра. Worker'у (системный контекст: задача в очереди
  считается доверенной).
- `find_by_id_for_user` / `list_recent_by_user` — с фильтром по владельцу.
  HTTP-слою, чтобы юзер не получил чужую запись.
"""
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.dto.generation import (
    GenerationListItemTransfer,
    GenerationTransfer,
)
from app.generation.domain.models.entity import GenerationEntity


class GenerationRepository:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    # ─── System-context (worker) ────────────────────────────────────────────
    async def find_by_id(self, gen_id: int) -> GenerationTransfer | None:
        async with self._session_factory() as session:
            entity = await session.get(GenerationEntity, gen_id)
            return GenerationTransfer.model_validate(entity) if entity else None

    # ─── User-scoped (HTTP layer) ───────────────────────────────────────────
    async def find_by_id_for_user(
        self,
        gen_id: int,
        user_id: int,
    ) -> GenerationTransfer | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(GenerationEntity).where(
                    GenerationEntity.id == gen_id,
                    GenerationEntity.user_id == user_id,
                )
            )
            entity = result.scalar_one_or_none()
            return GenerationTransfer.model_validate(entity) if entity else None

    async def list_recent_by_user(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[GenerationListItemTransfer]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(GenerationEntity)
                .where(GenerationEntity.user_id == user_id)
                .order_by(desc(GenerationEntity.created_at))
                .limit(limit)
            )
            return [
                GenerationListItemTransfer.model_validate(e)
                for e in result.scalars().all()
            ]
