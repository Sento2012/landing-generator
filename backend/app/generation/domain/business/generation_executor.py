"""GenerationExecutor — выполнение генерации в Celery-воркере.

Берёт pending-запись, помечает running, гоняет LLM-стрим, шлёт каждое
ключевое событие в RabbitMQ (notifier) для WS-клиентов и сохраняет финальный
результат / ошибку в БД.
"""
from app.generation.domain.models.status import GenerationStatus
from app.generation.domain.persistence.entity_manager import GenerationEntityManager
from app.generation.domain.persistence.repository import GenerationRepository
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm.domain.facade import LlmFacade
from app.llm.domain.models.llm_provider_name import LlmProviderName
from app.notifier.domain.business.routing import (
    NotificationTopic,
    routing_key_for_user,
)
from app.notifier.domain.dto.notification import NotificationTransfer
from app.notifier.domain.facade import NotifierFacade


class GenerationExecutor:
    def __init__(
        self,
        repository: GenerationRepository,
        entity_manager: GenerationEntityManager,
        llm_facade: LlmFacade,
        notifier_facade: NotifierFacade,
    ) -> None:
        self._repo = repository
        self._em = entity_manager
        self._llm = llm_facade
        self._notifier = notifier_facade

    async def execute(self, gen_id: int) -> None:
        gen = await self._repo.find_by_id(gen_id)
        if gen is None:
            return
        if gen.status != GenerationStatus.PENDING:
            return

        await self._em.mark_running(gen_id)
        await self._publish(gen.user_id, gen_id, status=GenerationStatus.RUNNING)

        try:
            llm_dto = LlmPromptTransfer(
                prompt=gen.prompt,
                provider=LlmProviderName(gen.provider),
            )
            final_result: LandingResultTransfer | None = None
            async for event in self._llm.stream_landing(llm_dto):
                await self._publish_event(gen.user_id, gen_id, event)
                if event.type == LlmEventType.DONE:
                    final_result = event.result
                elif event.type == LlmEventType.ERROR:
                    await self._em.mark_failed(gen_id, event.message or "unknown error")
                    return

            if final_result is not None:
                await self._em.save_result(gen_id, final_result)
                await self._publish(
                    gen.user_id, gen_id, status=GenerationStatus.COMPLETED,
                )
        except Exception as e:
            await self._em.mark_failed(gen_id, str(e))
            await self._publish(
                gen.user_id, gen_id,
                status=GenerationStatus.FAILED, message=str(e),
            )

    async def _publish_event(
        self, user_id: int, gen_id: int, event: LlmEventTransfer,
    ) -> None:
        payload = {"gen_id": gen_id, **event.model_dump(exclude_none=True)}
        await self._notifier.publish(
            NotificationTransfer(
                routing_key=routing_key_for_user(user_id, NotificationTopic.GENERATION),
                payload=payload,
            )
        )

    async def _publish(
        self,
        user_id: int,
        gen_id: int,
        *,
        status: GenerationStatus,
        message: str | None = None,
    ) -> None:
        payload: dict = {"gen_id": gen_id, "type": "status", "status": status.value}
        if message is not None:
            payload["message"] = message
        await self._notifier.publish(
            NotificationTransfer(
                routing_key=routing_key_for_user(user_id, NotificationTopic.GENERATION),
                payload=payload,
            )
        )
