"""Celery task — worker-side entry point для генерации.

Тонкий мост между sync Celery worker'ом и async business логикой Generation.
Получает gen_id из очереди, через composition root зовёт GenerationFacade.
"""
import asyncio

from app.generation.domain.business.task_names import GENERATION_RUN
from worker.celery_app import celery_app


@celery_app.task(name=GENERATION_RUN)
def run_generation_task(gen_id: int) -> None:
    asyncio.run(_run_async(gen_id))


async def _run_async(gen_id: int) -> None:
    from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
    from app.shared.dependency_provider import get_generation_facade

    facade = get_generation_facade()
    await facade.execute_generation(GenerationByIdTransfer(id=gen_id))
