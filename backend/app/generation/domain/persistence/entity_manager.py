"""EntityManager — операции ЗАПИСИ генераций."""
from datetime import datetime

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.models.entity import GenerationEntity
from app.generation.domain.models.status import GenerationStatus
from app.generation.domain.dto.generation import GenerationTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.llm.domain.dto.landing_result import LandingResultTransfer


class GenerationEntityManager:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        default_provider: str,
    ) -> None:
        self._session_factory = session_factory
        self._default_provider = default_provider

    async def create(self, dto: GenerationCreateTransfer) -> GenerationTransfer:
        provider = str(dto.provider) if dto.provider else self._default_provider
        async with self._session_factory() as session:
            entity = GenerationEntity(
                user_id=dto.user_id,
                prompt=dto.prompt,
                status=GenerationStatus.PENDING,
                provider=provider,
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return GenerationTransfer.model_validate(entity)

    async def mark_running(self, gen_id: int) -> None:
        await self._set_status(gen_id, GenerationStatus.RUNNING)

    async def mark_failed(self, gen_id: int, error: str) -> None:
        async with self._session_factory() as session:
            entity = await session.get(GenerationEntity, gen_id)
            if entity is None:
                return
            entity.status = GenerationStatus.FAILED
            entity.error = error
            entity.completed_at = datetime.utcnow()
            await session.commit()

    async def save_result(self, gen_id: int, result: LandingResultTransfer) -> None:
        async with self._session_factory() as session:
            entity = await session.get(GenerationEntity, gen_id)
            if entity is None:
                return
            entity.html = result.html
            entity.css = result.css
            entity.js = result.js
            entity.status = GenerationStatus.COMPLETED
            entity.completed_at = datetime.utcnow()
            await session.commit()

    async def _set_status(self, gen_id: int, status: GenerationStatus) -> None:
        async with self._session_factory() as session:
            entity = await session.get(GenerationEntity, gen_id)
            if entity is None:
                return
            entity.status = status
            await session.commit()
