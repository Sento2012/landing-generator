"""Бизнес-логика Anthropic: streaming, parsing tool_use blocks, сборка результата.

Здесь живёт всё Anthropic-специфичное. SYSTEM_PROMPT приходит параметром.
"""
from typing import AsyncIterator

import anthropic

from app.llm.domain.business.landing_result_builder import apply_tool_content
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm_anthropic.domain.models.chunk_event_types import (
    AnthropicBlockType,
    AnthropicChunkType,
    AnthropicDeltaType,
)


class AnthropicStreamLandingService:
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

    # ─── Public ──────────────────────────────────────────────────────────────
    async def stream(
        self,
        dto: LlmPromptTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        """Главный сценарий: открыть стрим, транслировать чанки в события,
        собрать финальный результат."""
        try:
            async with self._open_stream(dto.prompt) as stream:
                async for event in self._translate_chunks(stream):
                    yield event
                final_message = await stream.get_final_message()

            yield LlmEventTransfer(
                type=LlmEventType.DONE,
                result=self._extract_landing_result(final_message),
            )
        except anthropic.APIError as e:
            yield LlmEventTransfer(
                type=LlmEventType.ERROR,
                message=f"Anthropic API error: {e}",
            )
        except Exception as e:
            yield LlmEventTransfer(
                type=LlmEventType.ERROR,
                message=f"{type(e).__name__}: {e}",
            )

    # ─── Steps ───────────────────────────────────────────────────────────────
    def _open_stream(self, prompt: str):
        """Открыть async context manager стрима Anthropic с нашими параметрами."""
        return self._client.messages.stream(
            model=self._model,
            max_tokens=16000,
            system=[
                {
                    "type": "text",
                    "text": self._system_prompt,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            tools=self._tools,
            messages=[{"role": "user", "content": prompt}],
        )

    async def _translate_chunks(self, stream) -> AsyncIterator[LlmEventTransfer]:
        """Транслировать сырые Anthropic-чанки в наш формат событий.

        Состояние: имя текущего активного tool'а (которое пришло в content_block_start
        и нужно для последующих delta/stop в том же блоке).
        """
        current_tool: str | None = None

        async for chunk in stream:
            if chunk.type == AnthropicChunkType.CONTENT_BLOCK_START:
                event, current_tool = self._on_block_start(chunk)
            elif chunk.type == AnthropicChunkType.CONTENT_BLOCK_DELTA:
                event = self._on_block_delta(chunk, current_tool)
            elif chunk.type == AnthropicChunkType.CONTENT_BLOCK_STOP:
                event = self._on_block_stop(current_tool)
                current_tool = None
            else:
                event = None

            if event is not None:
                yield event

    # ─── Chunk handlers ──────────────────────────────────────────────────────
    @staticmethod
    def _on_block_start(chunk) -> tuple[LlmEventTransfer | None, str | None]:
        """content_block_start → если tool_use, открываем tool."""
        block = chunk.content_block
        if block.type != AnthropicBlockType.TOOL_USE:
            return None, None
        return (
            LlmEventTransfer(type=LlmEventType.TOOL_START, tool=block.name),
            block.name,
        )

    @staticmethod
    def _on_block_delta(chunk, current_tool: str | None) -> LlmEventTransfer | None:
        """content_block_delta → если идут куски JSON для текущего tool'а, шлём."""
        if current_tool is None:
            return None
        if chunk.delta.type != AnthropicDeltaType.INPUT_JSON_DELTA:
            return None
        return LlmEventTransfer(
            type=LlmEventType.TOOL_DELTA,
            tool=current_tool,
            partial=chunk.delta.partial_json,
        )

    @staticmethod
    def _on_block_stop(current_tool: str | None) -> LlmEventTransfer | None:
        """content_block_stop → закрываем текущий tool, если был."""
        if current_tool is None:
            return None
        return LlmEventTransfer(type=LlmEventType.TOOL_COMPLETE, tool=current_tool)

    # ─── Final extraction ────────────────────────────────────────────────────
    @staticmethod
    def _extract_landing_result(final_message) -> LandingResultTransfer:
        """Из tool_use блоков финального сообщения собрать html/css/js.

        Routing tool_name → result.* делает общий helper из llm/domain/business/.
        """
        result = LandingResultTransfer()
        for block in final_message.content:
            if getattr(block, "type", None) != AnthropicBlockType.TOOL_USE:
                continue
            content = (block.input or {}).get("content", "")
            apply_tool_content(result, block.name, content)
        return result
