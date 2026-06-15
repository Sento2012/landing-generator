"""GenerationExecutor — собственно выполнение генерации.

Запускается из Celery-задачи. Берёт pending-запись, помечает running,
дёргает LLM, сохраняет результат / ошибку.

Не yield'ит события — события для SSE стримит отдельный сервис (Generator/watcher),
который polls БД.
"""
from app.generation.domain.models.status import GenerationStatus
from app.generation.domain.persistence.entity_manager import GenerationEntityManager
from app.generation.domain.persistence.repository import GenerationRepository
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm.domain.facade import LlmFacade
from app.llm.domain.models.llm_provider_name import LlmProviderName


class GenerationExecutor:
    def __init__(
        self,
        repository: GenerationRepository,
        entity_manager: GenerationEntityManager,
        llm_facade: LlmFacade,
    ) -> None:
        self._repo = repository
        self._em = entity_manager
        self._llm = llm_facade

    async def execute(self, gen_id: int) -> None:
        gen = await self._repo.find_by_id(gen_id)
        if gen is None:
            return
        # Идемпотентность: если уже не pending — не дёргать LLM повторно.
        if gen.status != GenerationStatus.PENDING:
            return

        await self._em.mark_running(gen_id)

        try:
            llm_dto = LlmPromptTransfer(
                prompt=gen.prompt,
                provider=LlmProviderName(gen.provider),
            )
            final_result: LandingResultTransfer | None = None
            async for event in self._llm.stream_landing(llm_dto):
                if event.type == LlmEventType.DONE:
                    final_result = event.result
                elif event.type == LlmEventType.ERROR:
                    await self._em.mark_failed(gen_id, event.message or "unknown error")
                    return

            if final_result is not None:
                await self._em.save_result(gen_id, final_result)
        except Exception as e:
            await self._em.mark_failed(gen_id, str(e))
