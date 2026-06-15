"""Celery task — обёртка над GenerationExecutor для запуска в фоне.

Celery sync-first, поэтому внутри запускаем asyncio.run() на новом event loop'е.
"""
import asyncio

from app.generation.domain.business.task_names import GENERATION_RUN
from app.shared.celery_app import celery_app


@celery_app.task(name=GENERATION_RUN)
def run_generation_task(gen_id: int) -> None:
    asyncio.run(_run_async(gen_id))


async def _run_async(gen_id: int) -> None:
    from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
    from app.shared.dependency_provider import get_generation_facade

    facade = get_generation_facade()
    await facade.execute_generation(GenerationByIdTransfer(id=gen_id))
