"""Публичная дверь LlmOpenAi-модуля. Тонкая — делегирует Factory."""
from collections.abc import AsyncIterator

from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm_openai.domain.factory import OpenAiFactory


class OpenAiFacade:
    def __init__(self, factory: OpenAiFactory) -> None:
        self._factory = factory

    async def stream_landing(
        self,
        dto: LlmPromptTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        service = self._factory.create_stream_landing_service()
        async for event in service.stream(dto):
            yield event
