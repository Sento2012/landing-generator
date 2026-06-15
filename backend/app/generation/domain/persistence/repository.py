"""Repository — операции ЧТЕНИЯ генераций."""
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.models.entity import GenerationEntity
from app.generation.domain.dto.generation import (
    GenerationListItemTransfer,
    GenerationTransfer,
)


class GenerationRepository:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, gen_id: int) -> GenerationTransfer | None:
        async with self._session_factory() as session:
            entity = await session.get(GenerationEntity, gen_id)
            return GenerationTransfer.model_validate(entity) if entity else None

    async def list_recent(self, limit: int = 50) -> list[GenerationListItemTransfer]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(GenerationEntity)
                .order_by(desc(GenerationEntity.created_at))
                .limit(limit)
            )
            return [
                GenerationListItemTransfer.model_validate(e)
                for e in result.scalars().all()
            ]
