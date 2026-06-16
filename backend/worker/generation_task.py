"""Celery task — worker-side entry point для генерации.

Тонкий мост между sync Celery worker'ом и async business логикой Generation.
Получает gen_id из очереди, через composition root зовёт GenerationFacade.

Важно: после каждой задачи мы делаем engine.dispose(). Celery prefork
запускает несколько task'ов подряд в одном процессе, каждая через свой
asyncio.run() = свой event loop. Без dispose pool оставляет connections,
привязанные к старому loop'у, и следующая task падает с
"got Future attached to a different loop".
"""
import asyncio

from app.generation.domain.business.task_names import GENERATION_RUN
from worker.celery_app import celery_app


@celery_app.task(name=GENERATION_RUN)
def run_generation_task(gen_id: int) -> None:
    asyncio.run(_run_async(gen_id))


async def _run_async(gen_id: int) -> None:
    from app.generation.domain.dto.generation_execute import GenerationExecuteTransfer
    from app.shared.database import engine
    from app.shared.dependency_provider import (
        get_generation_facade,
        get_notifier_facade,
    )

    facade = get_generation_facade()
    try:
        await facade.execute_generation(GenerationExecuteTransfer(id=gen_id))
    finally:
        # См. docstring модуля. То же самое касается AMQP-коннекта notifier'а —
        # он привязан к event loop этой таски.
        await get_notifier_facade().close()
        await engine.dispose()
