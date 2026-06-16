"""Factory модуля notifier."""
import aio_pika

from app.notifier.domain.business.exchange_names import ExchangeName
from app.notifier.domain.business.publisher import NotificationPublisher
from app.notifier.domain.business.subscriber import NotificationSubscriber


class NotifierFactory:
    def __init__(self, amqp_url: str) -> None:
        self._amqp_url = amqp_url

    def create_publisher(self) -> NotificationPublisher:
        return NotificationPublisher(
            amqp_url=self._amqp_url,
            exchange_name=ExchangeName.NOTIFICATIONS,
        )

    def create_subscriber(
        self,
        connection: aio_pika.abc.AbstractRobustConnection,
    ) -> NotificationSubscriber:
        return NotificationSubscriber(
            connection=connection,
            exchange_name=ExchangeName.NOTIFICATIONS,
        )
