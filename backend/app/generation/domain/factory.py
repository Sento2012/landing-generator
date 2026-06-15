"""Factory модуля — собирает Repository / EntityManager / Generator с их зависимостями."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.business.generator import GenerationStreamingGenerator
from app.generation.domain.persistence.entity_manager import GenerationEntityManager
from app.generation.domain.persistence.repository import GenerationRepository
from app.llm.domain.facade import LlmFacade


class GenerationFactory:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        llm_facade: LlmFacade,
        default_provider: str,
    ) -> None:
        self._session_factory = session_factory
        self._llm_facade = llm_facade
        self._default_provider = default_provider

    def create_repository(self) -> GenerationRepository:
        return GenerationRepository(self._session_factory)

    def create_entity_manager(self) -> GenerationEntityManager:
        return GenerationEntityManager(
            session_factory=self._session_factory,
            default_provider=self._default_provider,
        )

    def create_generator(self) -> GenerationStreamingGenerator:
        return GenerationStreamingGenerator(
            repository=self.create_repository(),
            entity_manager=self.create_entity_manager(),
            llm_facade=self._llm_facade,
        )
