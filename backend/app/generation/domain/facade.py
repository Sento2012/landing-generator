"""Публичная дверь Generation-модуля.

Каждый метод принимает Transfer на вход и возвращает Transfer / список Transfer /
AsyncIterator[Transfer]. Никаких голых int/str/dict.
"""
from typing import AsyncIterator

from app.generation.domain.factory import GenerationFactory
from app.generation.domain.dto.generation import GenerationTransfer
from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.dto.generation_list import GenerationListTransfer
from app.generation.domain.dto.generation_list_criteria import (
    GenerationListCriteriaTransfer,
)
from app.llm.domain.dto.llm_event import LlmEventTransfer


class GenerationFacade:
    def __init__(self, factory: GenerationFactory) -> None:
        self._factory = factory

    async def create_generation(
        self,
        dto: GenerationCreateTransfer,
    ) -> GenerationTransfer:
        return await self._factory.create_entity_manager().create(dto)

    async def get_generation(
        self,
        dto: GenerationByIdTransfer,
    ) -> GenerationTransfer | None:
        return await self._factory.create_repository().find_by_id(dto.id)

    async def list_generations(
        self,
        dto: GenerationListCriteriaTransfer,
    ) -> GenerationListTransfer:
        items = await self._factory.create_repository().list_recent(dto.limit)
        return GenerationListTransfer(items=items)

    async def stream_generation(
        self,
        dto: GenerationByIdTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        async for event in self._factory.create_generator().stream(dto.id):
            yield event
