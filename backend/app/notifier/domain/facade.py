"""Публичная дверь notifier-модуля для publisher-side (worker/HTTP).

Subscriber-side (WS-сервис) использует Factory.create_subscriber напрямую,
потому что владеет своим долгоживущим RabbitMQ-соединением.
"""
from app.notifier.domain.business.publisher import NotificationPublisher
from app.notifier.domain.dto.notification import NotificationTransfer
from app.notifier.domain.factory import NotifierFactory


class NotifierFacade:
    def __init__(self, factory: NotifierFactory) -> None:
        self._factory = factory
        self._publisher: NotificationPublisher | None = None

    async def publish(self, dto: NotificationTransfer) -> None:
        if self._publisher is None:
            self._publisher = self._factory.create_publisher()
        await self._publisher.publish(dto)

    async def close(self) -> None:
        if self._publisher is not None:
            await self._publisher.close()
            self._publisher = None
