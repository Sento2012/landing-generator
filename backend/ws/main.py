"""WebSocket gateway — отдельный FastAPI-сервис.

После логина клиент держит один WS-коннект на /ws?token=<JWT>. Сервис:
- валидирует токен (без обращения в БД — только проверка подписи),
- открывает временную очередь в RabbitMQ, биндит её на `user.<id>.*`
  topic-exchange'а `notifications`,
- форвардит каждое сообщение в сокет,
- держит коннект живым через app-level ping/pong с idle-таймаутом 60с.

Один процесс — одно AMQP-соединение (через lifespan). На каждое WS-подключение
заводится свой channel + queue, при закрытии всё освобождается.
"""
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, status

from app.notifier.domain.business.exchange_names import ExchangeName
from app.notifier.domain.business.routing import routing_pattern_for_user
from app.notifier.domain.business.subscriber import NotificationSubscriber
from app.shared.dependency_provider import get_user_facade
from app.user.domain.business.jwt_service import InvalidTokenError

logger = logging.getLogger("ws")
logging.basicConfig(level=logging.INFO)

IDLE_TIMEOUT_SECONDS = 60
AMQP_URL = os.environ.get(
    "AMQP_URL",
    os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.amqp = await aio_pika.connect_robust(AMQP_URL)
    logger.info("ws-gateway: AMQP connected")
    try:
        yield
    finally:
        await app.state.amqp.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        payload = get_user_facade().decode_token(token)
    except InvalidTokenError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token",
        )
        return

    await websocket.accept()
    user_id = payload.user_id
    logger.info("WS open user=%s", user_id)

    subscriber = NotificationSubscriber(
        connection=websocket.app.state.amqp,
        exchange_name=ExchangeName.NOTIFICATIONS,
    )

    forward_task = asyncio.create_task(
        _forward_amqp_to_socket(websocket, subscriber, user_id)
    )

    try:
        await _read_loop(websocket, user_id)
    except WebSocketDisconnect:
        logger.info("WS disconnect user=%s", user_id)
    finally:
        forward_task.cancel()
        try:
            await forward_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass


async def _read_loop(websocket: WebSocket, user_id: int) -> None:
    """Читает фрейм с idle-таймаутом. Обрабатывает только ping (отвечает pong)."""
    while True:
        try:
            raw = await asyncio.wait_for(
                websocket.receive_text(), timeout=IDLE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.info("WS idle timeout user=%s", user_id)
            await websocket.close(
                code=status.WS_1000_NORMAL_CLOSURE, reason="idle timeout",
            )
            return

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if msg.get("type") == "ping":
            logger.info("WS ping ← user=%s; pong →", user_id)
            await websocket.send_text(json.dumps({"type": "pong"}))


async def _forward_amqp_to_socket(
    websocket: WebSocket,
    subscriber: NotificationSubscriber,
    user_id: int,
) -> None:
    try:
        async for payload in subscriber.subscribe(routing_pattern_for_user(user_id)):
            await websocket.send_text(json.dumps(payload))
    except asyncio.CancelledError:
        raise
    except Exception as e:  # noqa: BLE001
        logger.warning("WS forward error user=%s: %s", user_id, e)
