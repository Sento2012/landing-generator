"""Контракт LLM-провайдера. Всё, что внешний код знает о провайдере."""
from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.llm.domain.dto.llm_event import LlmEventTransfer


class LlmProviderPluginInterface(ABC):
    """Базовый интерфейс плагина LLM-провайдера.

    Реализации (OpenAi, Anthropic, ...) живут в отдельных модулях
    и подключаются через dependency_provider.
    """

    @abstractmethod
    def stream_landing(
        self,
        prompt: str,
    ) -> AsyncIterator[LlmEventTransfer]:
        """Стримит события генерации лендинга.

        Реализации обычно — async-генераторы:
            async def stream_landing(self, prompt):
                yield LlmEventTransfer(type="tool_start", tool="set_html")
                ...

        Гарантии:
        - Последним событием идёт либо type="done" с заполненным result,
          либо type="error" с message.
        - tool_start/tool_complete/tool_delta могут отсутствовать
          (если провайдер не поддерживает стриминг tool calls).
        """
        ...
