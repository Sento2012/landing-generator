"""GenerationScheduler — оркестратор постановки генерации в очередь.

Делает две вещи атомарно с точки зрения user-сценария:
1. Сохраняет запись в БД (status=pending).
2. Публикует task в очередь.
"""
from app.generation.domain.business.task_names import GENERATION_QUEUE, GENERATION_RUN
from app.generation.domain.dto.generation import GenerationTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.persistence.entity_manager import GenerationEntityManager
from app.rabbitmq.domain.dto.task_message import TaskMessage
from app.rabbitmq.domain.facade import RabbitmqFacade


class GenerationScheduler:
    def __init__(
        self,
        entity_manager: GenerationEntityManager,
        rabbitmq_facade: RabbitmqFacade,
    ) -> None:
        self._em = entity_manager
        self._rabbitmq = rabbitmq_facade

    async def schedule(self, dto: GenerationCreateTransfer) -> GenerationTransfer:
        gen = await self._em.create(dto)
        self._rabbitmq.publish_task(
            TaskMessage(
                task_name=GENERATION_RUN,
                args=[gen.id],
                queue=GENERATION_QUEUE,
            )
        )
        return gen
