"""Factory модуля — собирает сервисы Generation домена."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.business.generation_executor import GenerationExecutor
from app.generation.domain.business.generation_scheduler import GenerationScheduler
from app.generation.domain.business.generator import GenerationStreamingGenerator
from app.generation.domain.persistence.entity_manager import GenerationEntityManager
from app.generation.domain.persistence.repository import GenerationRepository
from app.llm.domain.facade import LlmFacade
from app.rabbitmq.domain.facade import RabbitmqFacade


class GenerationFactory:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        llm_facade: LlmFacade,
        rabbitmq_facade: RabbitmqFacade,
        default_provider: str,
    ) -> None:
        self._session_factory = session_factory
        self._llm_facade = llm_facade
        self._rabbitmq_facade = rabbitmq_facade
        self._default_provider = default_provider

    def create_repository(self) -> GenerationRepository:
        return GenerationRepository(self._session_factory)

    def create_entity_manager(self) -> GenerationEntityManager:
        return GenerationEntityManager(
            session_factory=self._session_factory,
            default_provider=self._default_provider,
        )

    def create_generator(self) -> GenerationStreamingGenerator:
        return GenerationStreamingGenerator(repository=self.create_repository())

    def create_executor(self) -> GenerationExecutor:
        return GenerationExecutor(
            repository=self.create_repository(),
            entity_manager=self.create_entity_manager(),
            llm_facade=self._llm_facade,
        )

    def create_scheduler(self) -> GenerationScheduler:
        return GenerationScheduler(
            entity_manager=self.create_entity_manager(),
            rabbitmq_facade=self._rabbitmq_facade,
        )
