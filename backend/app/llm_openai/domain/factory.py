"""Factory модуля LlmOpenAi — создаёт сервисы из готовых зависимостей."""
from openai import AsyncOpenAI

from app.llm_openai.domain.business.stream_landing_service import OpenAiStreamLandingService


class OpenAiFactory:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        tools: list[dict],
        system_prompt: str,
    ) -> None:
        self._client = client
        self._model = model
        self._tools = tools
        self._system_prompt = system_prompt

    def create_stream_landing_service(self) -> OpenAiStreamLandingService:
        return OpenAiStreamLandingService(
            client=self._client,
            model=self._model,
            tools=self._tools,
            system_prompt=self._system_prompt,
        )
