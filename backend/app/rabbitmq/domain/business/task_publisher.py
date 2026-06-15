"""TaskPublisher — отправляет task-message в брокер через Celery `send_task`.

Не импортирует конкретные task'и — работает по строковому имени. Это позволяет
этому модулю не знать ни про Generation, ни про другие домены.
"""
from celery import Celery

from app.rabbitmq.domain.dto.task_message import TaskMessage


class TaskPublisher:
    def __init__(self, celery_app: Celery) -> None:
        self._celery = celery_app

    def publish(self, message: TaskMessage) -> None:
        self._celery.send_task(
            message.task_name,
            args=message.args,
            kwargs=message.kwargs,
        )
