"""Celery task — обёртка над GenerationExecutor для запуска в фоне.

Celery sync-first, поэтому внутри запускаем asyncio.run() на новом event loop'е
(один на вызов task'а — Celery worker форкается, всё чисто).
"""
import asyncio

from app.shared.celery_app import celery_app


@celery_app.task(name="generation.run", bind=True, max_retries=0)
def run_generation_task(self, gen_id: int) -> None:
    asyncio.run(_run_async(gen_id))


async def _run_async(gen_id: int) -> None:
    # Импортим внутри функции, чтобы избежать цепочки import'ов на этапе
    # загрузки модуля Celery (включает app.* до того, как event loop готов).
    from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
    from app.shared.dependency_provider import get_generation_facade

    facade = get_generation_facade()
    await facade.execute_generation(GenerationByIdTransfer(id=gen_id))
