"""Публичная дверь Llm-модуля. Тонкая — делегирует Factory."""
from typing import AsyncIterator

from app.llm.domain.factory import LlmFactory
from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer


class LlmFacade:
    def __init__(self, factory: LlmFactory) -> None:
        self._factory = factory

    async def stream_landing(
        self,
        dto: LlmPromptTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        """Запустить генерацию по промпту. Провайдер выбирается из dto.provider
        (если None — используется default из LlmFactory)."""
        plugin = self._factory.get_provider_plugin(dto.provider)
        async for event in plugin.stream_landing(dto.prompt):
            yield event
