"""Wiring модуля Rabbitmq."""
from celery import Celery

from app.rabbitmq.domain.facade import RabbitmqFacade
from app.rabbitmq.domain.factory import RabbitmqFactory


def build_rabbitmq_facade(celery_app: Celery) -> RabbitmqFacade:
    return RabbitmqFacade(RabbitmqFactory(celery_app))
