"""Публичная дверь Rabbitmq-модуля."""
from app.rabbitmq.domain.dto.task_message import TaskMessage
from app.rabbitmq.domain.factory import RabbitmqFactory


class RabbitmqFacade:
    def __init__(self, factory: RabbitmqFactory) -> None:
        self._factory = factory

    def publish_task(self, message: TaskMessage) -> None:
        self._factory.create_task_publisher().publish(message)
