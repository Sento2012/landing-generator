"""Generator — наблюдатель за прогрессом генерации для SSE.

Сам не делает LLM-работу — это задача Executor'а, который крутится в Celery worker.
Этот класс polls БД и эмитит события клиенту по смене статуса.

Granularity: мы видим переход pending → running → completed/failed.
Tool-by-tool deltas не доступны (для них нужен pub/sub между worker и SSE).
"""
import asyncio
from typing import AsyncIterator

from app.generation.domain.models.status import GenerationStatus
from app.generation.domain.persistence.repository import GenerationRepository
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType

POLL_INTERVAL_SECONDS = 0.5
MAX_WAIT_SECONDS = 600   # 10 минут — если за это время не завершилось, отдаём timeout


class GenerationStreamingGenerator:
    def __init__(self, repository: GenerationRepository) -> None:
        self._repo = repository

    async def stream(self, gen_id: int) -> AsyncIterator[LlmEventTransfer]:
        deadline = asyncio.get_event_loop().time() + MAX_WAIT_SECONDS
        emitted_running = False

        while True:
            gen = await self._repo.find_by_id(gen_id)
            if gen is None:
                yield LlmEventTransfer(
                    type=LlmEventType.ERROR,
                    message="generation not found",
                )
                return

            if gen.status == GenerationStatus.COMPLETED:
                yield LlmEventTransfer(
                    type=LlmEventType.DONE,
                    result=LandingResultTransfer(
                        html=gen.html or "",
                        css=gen.css or "",
                        js=gen.js or "",
                    ),
                )
                return

            if gen.status == GenerationStatus.FAILED:
                yield LlmEventTransfer(
                    type=LlmEventType.ERROR,
                    message=gen.error or "generation failed",
                )
                return

            if gen.status == GenerationStatus.RUNNING and not emitted_running:
                yield LlmEventTransfer(
                    type=LlmEventType.TOOL_START,
                    tool="generation",
                )
                emitted_running = True

            if asyncio.get_event_loop().time() > deadline:
                yield LlmEventTransfer(
                    type=LlmEventType.ERROR,
                    message="generation timed out",
                )
                return

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
