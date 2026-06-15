"""Wiring модуля Generation.

Знает, как собрать GenerationFacade с зависимостями (session_factory, LlmFacade,
default_provider). Сами зависимости приходят параметрами от composition root.
"""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.generation.domain.facade import GenerationFacade
from app.generation.domain.factory import GenerationFactory
from app.llm.domain.facade import LlmFacade


def build_generation_facade(
    session_factory: async_sessionmaker,
    llm_facade: LlmFacade,
    default_provider: str,
) -> GenerationFacade:
    """Собрать GenerationFacade со всеми зависимостями."""
    factory = GenerationFactory(
        session_factory=session_factory,
        llm_facade=llm_facade,
        default_provider=default_provider,
    )
    return GenerationFacade(factory)
