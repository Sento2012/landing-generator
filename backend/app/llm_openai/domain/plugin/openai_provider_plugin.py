"""Plugin — тонкий адаптер OpenAI-модуля к LlmProviderPluginInterface.

Логики здесь нет. Всё реальное — в OpenAiStreamLandingService через OpenAiFacade.
Plugin только переупаковывает `str → LlmPromptTransfer` и проксирует поток событий.
"""
from typing import AsyncIterator

from app.llm.domain.plugin.interface import LlmProviderPluginInterface
from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm_openai.domain.facade import OpenAiFacade


class OpenAiProviderPlugin(LlmProviderPluginInterface):
    def __init__(self, facade: OpenAiFacade) -> None:
        self._facade = facade

    async def stream_landing(
        self,
        prompt: str,
    ) -> AsyncIterator[LlmEventTransfer]:
        # Interface принимает str, наш модуль работает с DTO — упаковываем.
        async for event in self._facade.stream_landing(LlmPromptTransfer(prompt=prompt)):
            yield event
