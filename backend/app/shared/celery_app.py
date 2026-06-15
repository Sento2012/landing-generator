"""Celery application instance — broker = RabbitMQ.

Запуск воркера:
    celery -A app.shared.celery_app worker --loglevel=info

include= — модули с задачами, чтобы Celery их зарегистрировал при старте воркера.
Если добавится новая задача в другом модуле — добавить путь сюда.
"""
import os

from celery import Celery

celery_app = Celery(
    "landing_generator",
    broker=os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
    # rpc:// — result backend через тот же RabbitMQ, без Redis. Подходит для
    # коротких результатов (мы не используем .get() — задача пишет в БД сама).
    backend="rpc://",
    include=[
        "app.generation.domain.business.generation_task",
    ],
)

celery_app.conf.update(
    task_acks_late=True,           # ack только после успешной обработки
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # не хапать сразу пачку задач (генерации долгие)
    task_track_started=True,
)
