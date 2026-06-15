"""Generator — оркестратор стриминговой генерации.

Связывает Repository, EntityManager и LlmFacade. Знает сценарий:
  load → mark_running → stream from LLM → save_result | mark_failed.
"""
from typing import AsyncIterator

from app.generation.domain.persistence.entity_manager import GenerationEntityManager
from app.generation.domain.persistence.repository import GenerationRepository
from app.generation.domain.models.status import GenerationStatus
from app.llm.domain.facade import LlmFacade
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm.domain.models.llm_provider_name import LlmProviderName


class GenerationStreamingGenerator:
    def __init__(
        self,
        repository: GenerationRepository,
        entity_manager: GenerationEntityManager,
        llm_facade: LlmFacade,
    ) -> None:
        self._repo = repository
        self._em = entity_manager
        self._llm = llm_facade

    async def stream(self, gen_id: int) -> AsyncIterator[LlmEventTransfer]:
        gen = await self._repo.find_by_id(gen_id)
        if gen is None:
            yield LlmEventTransfer(type=LlmEventType.ERROR, message="generation not found")
            return

        # Уже выполнена — replay результата
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
                message=gen.error or "previous generation failed",
            )
            return

        # Pending / running — запускаем (или подхватываем, что эквивалентно — стрим заново)
        await self._em.mark_running(gen_id)

        final_result: LandingResultTransfer | None = None
        try:
            llm_dto = LlmPromptTransfer(
                prompt=gen.prompt,
                provider=LlmProviderName(gen.provider),
            )
            async for event in self._llm.stream_landing(llm_dto):
                if event.type == LlmEventType.DONE:
                    final_result = event.result
                elif event.type == LlmEventType.ERROR:
                    await self._em.mark_failed(gen_id, event.message or "unknown error")
                    yield event
                    return
                yield event

            if final_result is not None:
                await self._em.save_result(gen_id, final_result)
        except Exception as e:
            await self._em.mark_failed(gen_id, str(e))
            yield LlmEventTransfer(type=LlmEventType.ERROR, message=str(e))
