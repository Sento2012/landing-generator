"""Celery task — отправка email через SMTP.

Подключается к очереди EMAIL_QUEUE (см. celery_email_worker в docker-compose).
"""
import asyncio

from app.email.domain.business.task_names import EMAIL_SEND
from worker.celery_app import celery_app


@celery_app.task(name=EMAIL_SEND)
def send_email_task(message_dict: dict) -> None:
    asyncio.run(_run_async(message_dict))


async def _run_async(message_dict: dict) -> None:
    from app.email.domain.dto.email_message import EmailMessageTransfer
    from app.shared.dependency_provider import get_email_facade

    facade = get_email_facade()
    await facade.send_email(EmailMessageTransfer.model_validate(message_dict))
