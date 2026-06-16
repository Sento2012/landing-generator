"""Публичная дверь Llm-модуля. Тонкая — делегирует Factory."""
from collections.abc import AsyncIterator

from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm.domain.factory import LlmFactory


class LlmFacade:
    def __init__(self, factory: LlmFactory) -> None:
        self._factory = factory

    async def stream_landing(
        self,
        dto: LlmPromptTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        resolver = self._factory.create_plugin_resolver()
        plugin = resolver.resolve(dto.provider)
        async for event in plugin.stream_landing(dto.prompt):
            yield event
