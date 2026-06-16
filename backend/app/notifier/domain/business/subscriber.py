"""Подписчик на RabbitMQ topic exchange.

Создаёт эксклюзивную auto-delete очередь, биндит её к exchange по routing_pattern
(например `user.42.*`), отдаёт async iterator с распарсенными payload'ами.
При закрытии генератора (отмена / disconnect) channel явно закрывается —
тогда auto-delete queue гарантированно убирается на стороне брокера.
"""
import json
from typing import Any, AsyncIterator

import aio_pika


class NotificationSubscriber:
    def __init__(
        self,
        connection: aio_pika.abc.AbstractRobustConnection,
        exchange_name: str,
    ) -> None:
        self._connection = connection
        self._exchange_name = exchange_name

    async def subscribe(
        self, routing_pattern: str,
    ) -> AsyncIterator[dict[str, Any]]:
        channel = await self._connection.channel()
        try:
            await channel.set_qos(prefetch_count=32)
            exchange = await channel.declare_exchange(
                self._exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue("", exclusive=True, auto_delete=True)
            await queue.bind(exchange, routing_key=routing_pattern)

            async with queue.iterator() as iterator:
                async for message in iterator:
                    async with message.process():
                        yield json.loads(message.body.decode())
        finally:
            if not channel.is_closed:
                await channel.close()
