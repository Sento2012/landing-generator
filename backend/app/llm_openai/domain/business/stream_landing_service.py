"""Бизнес-логика OpenAI: streaming, parsing tool_calls, сборка результата.

SYSTEM_PROMPT приходит параметром — модуль не зависит от llm/domain/prompt.py.

Декомпозиция как у Anthropic-сервиса:
- stream() — сценарий
- _translate_chunks() — конвертация сырых OpenAI-чанков в наши события
- _on_*_chunk() — обработчики разных типов чанков
- _extract_landing_result() — финальная сборка из накопленных tool_calls
"""
import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI, OpenAIError

from app.llm.domain.business.landing_result_builder import apply_tool_content
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer

# Накопитель одного tool call: имя и аккумулированный JSON arguments.
_ToolCallAcc = dict[str, str]  # {"name": ..., "arguments": ...}


class OpenAiStreamLandingService:
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

    # ─── Public ──────────────────────────────────────────────────────────────
    async def stream(
        self,
        dto: LlmPromptTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        try:
            stream = await self._open_stream(dto.prompt)

            tool_calls: dict[int, _ToolCallAcc] = {}
            async for event in self._translate_chunks(stream, tool_calls):
                yield event

            yield LlmEventTransfer(
                type=LlmEventType.DONE,
                result=self._extract_landing_result(tool_calls),
            )
        except OpenAIError as e:
            yield LlmEventTransfer(
                type=LlmEventType.ERROR,
                message=f"OpenAI API error: {e}",
            )
        except Exception as e:
            yield LlmEventTransfer(
                type=LlmEventType.ERROR,
                message=f"{type(e).__name__}: {e}",
            )

    # ─── Steps ───────────────────────────────────────────────────────────────
    async def _open_stream(self, prompt: str):
        return await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
            tools=self._tools,
            tool_choice="auto",
            stream=True,
            max_tokens=16000,
        )

    async def _translate_chunks(
        self,
        stream,
        tool_calls: dict[int, _ToolCallAcc],
    ) -> AsyncIterator[LlmEventTransfer]:
        """Перевести сырые OpenAI-чанки в наши события.

        Состояние: текущий активный index tool_call'а (нужен для tool_complete
        при переключении на новый tool или в конце стрима). tool_calls
        мутируется снаружи — нам надо вернуть аккумулированные arguments
        для финальной сборки результата.
        """
        current_index: int | None = None

        async for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]

            for event, new_index in self._on_delta(choice.delta, tool_calls, current_index):
                current_index = new_index
                if event is not None:
                    yield event

            if choice.finish_reason and current_index is not None:
                yield LlmEventTransfer(
                    type=LlmEventType.TOOL_COMPLETE,
                    tool=tool_calls[current_index]["name"],
                )

    # ─── Chunk handlers ──────────────────────────────────────────────────────
    @staticmethod
    def _on_delta(
        delta,
        tool_calls: dict[int, _ToolCallAcc],
        current_index: int | None,
    ):
        """Один delta-чанк может содержать несколько tool_calls (редко, но возможно).

        Это generator-функция: yield'ит пары (event_or_None, new_current_index).
        Каждая итерация — обработка одного tool_call'а из чанка.
        """
        if not delta or not delta.tool_calls:
            return

        for tc in delta.tool_calls:
            idx = tc.index

            # Новый tool: закрываем предыдущий, открываем этот
            if idx not in tool_calls:
                if current_index is not None:
                    yield (
                        LlmEventTransfer(
                            type=LlmEventType.TOOL_COMPLETE,
                            tool=tool_calls[current_index]["name"],
                        ),
                        idx,
                    )
                name = (tc.function.name if tc.function else "") or ""
                tool_calls[idx] = {"name": name, "arguments": ""}
                current_index = idx
                if name:
                    yield (
                        LlmEventTransfer(type=LlmEventType.TOOL_START, tool=name),
                        idx,
                    )

            # Имя tool'а пришло отдельно от первого чанка (редкий кейс)
            if tc.function and tc.function.name and not tool_calls[idx]["name"]:
                tool_calls[idx]["name"] = tc.function.name
                yield (
                    LlmEventTransfer(
                        type=LlmEventType.TOOL_START,
                        tool=tc.function.name,
                    ),
                    idx,
                )

            # Куски JSON arguments
            if tc.function and tc.function.arguments:
                tool_calls[idx]["arguments"] += tc.function.arguments
                yield (
                    LlmEventTransfer(
                        type=LlmEventType.TOOL_DELTA,
                        tool=tool_calls[idx]["name"],
                        partial=tc.function.arguments,
                    ),
                    idx,
                )

    # ─── Final extraction ────────────────────────────────────────────────────
    @staticmethod
    def _extract_landing_result(
        tool_calls: dict[int, _ToolCallAcc],
    ) -> LandingResultTransfer:
        """Парсим накопленные tool_call.arguments как JSON и кладём в result."""
        result = LandingResultTransfer()
        for tc in tool_calls.values():
            try:
                args = json.loads(tc["arguments"])
            except json.JSONDecodeError:
                continue
            apply_tool_content(result, tc["name"], args.get("content", ""))
        return result
