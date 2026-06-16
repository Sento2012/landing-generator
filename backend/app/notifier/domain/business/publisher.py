"""Публикатор уведомлений в RabbitMQ topic exchange.

Подключение ленивое (на первый publish), переиспользуется до close().
Caller (Executor) обязан вызвать close() в finally — иначе соединение зависнет
до GC. В Celery-воркере event loop умирает после задачи, и каждое следующее
обращение откроет новое соединение в новом loop'е.
"""
import json

import aio_pika

from app.notifier.domain.dto.notification import NotificationTransfer


class NotificationPublisher:
    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        self._url = amqp_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def publish(self, dto: NotificationTransfer) -> None:
        await self._ensure_connected()
        assert self._exchange is not None
        await self._exchange.publish(
            aio_pika.Message(
                body=json.dumps(dto.payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
                content_type="application/json",
            ),
            routing_key=dto.routing_key,
        )

    async def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._exchange = None

    async def _ensure_connected(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            return
        self._connection = await aio_pika.connect_robust(self._url)
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            self._exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
