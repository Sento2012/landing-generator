"""Сборка NotifierFacade — вызывается из shared/dependency_provider."""
from app.notifier.domain.facade import NotifierFacade
from app.notifier.domain.factory import NotifierFactory


def build_notifier_facade(amqp_url: str) -> NotifierFacade:
    return NotifierFacade(factory=NotifierFactory(amqp_url=amqp_url))
