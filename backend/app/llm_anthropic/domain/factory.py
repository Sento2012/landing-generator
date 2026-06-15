"""Factory модуля LlmAnthropic — создаёт сервисы из готовых зависимостей."""
import anthropic

from app.llm_anthropic.domain.business.stream_landing_service import (
    AnthropicStreamLandingService,
)


class AnthropicFactory:
    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        model: str,
        tools: list[dict],
        system_prompt: str,
    ) -> None:
        self._client = client
        self._model = model
        self._tools = tools
        self._system_prompt = system_prompt

    def create_stream_landing_service(self) -> AnthropicStreamLandingService:
        return AnthropicStreamLandingService(
            client=self._client,
            model=self._model,
            tools=self._tools,
            system_prompt=self._system_prompt,
        )
