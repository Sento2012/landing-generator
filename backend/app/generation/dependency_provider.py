"""Wiring модуля Generation."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.facade import GenerationFacade
from app.generation.domain.factory import GenerationFactory
from app.llm.domain.facade import LlmFacade
from app.rabbitmq.domain.facade import RabbitmqFacade


def build_generation_facade(
    session_factory: async_sessionmaker,
    llm_facade: LlmFacade,
    rabbitmq_facade: RabbitmqFacade,
    default_provider: str,
) -> GenerationFacade:
    factory = GenerationFactory(
        session_factory=session_factory,
        llm_facade=llm_facade,
        rabbitmq_facade=rabbitmq_facade,
        default_provider=default_provider,
    )
    return GenerationFacade(factory)
