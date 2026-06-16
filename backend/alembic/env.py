"""Alembic env — async + autogenerate против наших ORM-сущностей.

DATABASE_URL берётся из env (или из alembic.ini как fallback).
Все entity'и явно импортятся ниже, чтобы Base.metadata их видел.
"""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ─── ORM metadata target ─────────────────────────────────────────────────────
# Импорт нужен, чтобы Base.metadata знала про таблицы. Каждый раз когда
# в проекте появляется новая entity — импортить её тут.
from app.shared.database import Base  # noqa: E402
from app.generation.domain.models import entity as _gen_entity  # noqa: E402, F401
from app.user.domain.models import entity as _user_entity  # noqa: E402, F401


config = context.config

# DATABASE_URL приоритетнее sqlalchemy.url из alembic.ini
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,             # ловить изменения типов колонок
        compare_server_default=True,   # ловить изменения default'ов
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    # Offline mode (генерация SQL без подключения к БД) не настраиваем —
    # не используем в нашем флоу.
    raise NotImplementedError("offline mode not supported in this project")
else:
    run_migrations_online()
