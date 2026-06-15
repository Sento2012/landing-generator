"""Factory модуля Rabbitmq — создаёт публишеры из готового Celery-app."""
from celery import Celery

from app.rabbitmq.domain.business.task_publisher import TaskPublisher


class RabbitmqFactory:
    def __init__(self, celery_app: Celery) -> None:
        self._celery_app = celery_app

    def create_task_publisher(self) -> TaskPublisher:
        return TaskPublisher(self._celery_app)
