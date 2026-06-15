"""Generic SSE-обёртка для FastAPI StreamingResponse.

Базовая инфра — не привязана ни к какому модулю. Подходит для любого
AsyncIterator[BaseModel], где у модели есть поле `type: str`
(используется как имя SSE-события).
"""
import json
from typing import AsyncIterator

from fastapi.responses import StreamingResponse
from pydantic import BaseModel


def _to_sse_message(event: BaseModel) -> str:
    """Pydantic-модель → одно SSE-сообщение.

    Формат:
        event: <type>      ← берётся из поля event.type, иначе "message"
        data: <json>
        \\n\\n
    """
    data = event.model_dump(exclude_none=True, mode="json")
    event_type = data.get("type", "message")
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_as_sse(events: AsyncIterator[BaseModel]) -> StreamingResponse:
    """AsyncIterator[Pydantic event] → готовый HTTP StreamingResponse с SSE-форматом.

    Заголовки:
    - text/event-stream — обязательный MIME для SSE.
    - Cache-Control: no-cache — браузеры не кешируют стрим.
    - X-Accel-Buffering: no — отключает буферизацию nginx в проде.
    """

    async def _generate():
        async for event in events:
            yield _to_sse_message(event)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
