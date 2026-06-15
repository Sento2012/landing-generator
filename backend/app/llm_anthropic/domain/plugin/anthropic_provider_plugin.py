"""Plugin — тонкий адаптер Anthropic-модуля к LlmProviderPluginInterface.

Логики здесь нет. Всё реальное — в AnthropicStreamLandingService через AnthropicFacade.
Plugin только переупаковывает `str → LlmPromptTransfer` и проксирует поток событий.
"""
from typing import AsyncIterator

from app.llm.domain.plugin.interface import LlmProviderPluginInterface
from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm_anthropic.domain.facade import AnthropicFacade


class AnthropicProviderPlugin(LlmProviderPluginInterface):
    def __init__(self, facade: AnthropicFacade) -> None:
        self._facade = facade

    async def stream_landing(
        self,
        prompt: str,
    ) -> AsyncIterator[LlmEventTransfer]:
        async for event in self._facade.stream_landing(LlmPromptTransfer(prompt=prompt)):
            yield event
