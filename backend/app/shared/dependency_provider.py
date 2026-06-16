"""Composition root приложения.

Единственное место, которое:
- читает env-переменные,
- знает обо ВСЕХ модулях и подключаемых плагинах,
- кеширует собранные Facade (один инстанс на жизнь app),
- отдаёт их FastAPI через Depends().
"""
import os
from functools import lru_cache

from app.email.dependency_provider import build_email_facade
from app.email.domain.facade import EmailFacade
from app.generation.dependency_provider import build_generation_facade
from app.generation.domain.facade import GenerationFacade
from app.llm.dependency_provider import build_llm_facade
from app.llm.domain.facade import LlmFacade
from app.llm.domain.models.llm_provider_name import LlmProviderName
from app.llm.domain.prompt import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from app.llm_anthropic.dependency_provider import build_anthropic_plugin
from app.llm_openai.dependency_provider import build_openai_plugin
from app.notifier.dependency_provider import build_notifier_facade
from app.notifier.domain.facade import NotifierFacade
from app.rabbitmq.dependency_provider import build_rabbitmq_facade
from app.rabbitmq.domain.facade import RabbitmqFacade
from app.shared.database import SessionLocal
from app.user.dependency_provider import build_user_facade
from app.user.domain.facade import UserFacade
from worker.celery_app import celery_app


DEFAULT_LLM_PROVIDER = LlmProviderName(
    os.environ.get("LLM_PROVIDER", LlmProviderName.OPENAI)
)


# ─── Llm Facade ──────────────────────────────────────────────────────────────
@lru_cache
def get_llm_facade() -> LlmFacade:
    plugins = {
        LlmProviderName.OPENAI: build_openai_plugin(
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            system_prompt=SYSTEM_PROMPT,
            tool_descriptions=TOOL_DESCRIPTIONS,
        ),
        LlmProviderName.ANTHROPIC: build_anthropic_plugin(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            system_prompt=SYSTEM_PROMPT,
            tool_descriptions=TOOL_DESCRIPTIONS,
        ),
    }
    return build_llm_facade(plugins=plugins, default=DEFAULT_LLM_PROVIDER)


# ─── Rabbitmq Facade ─────────────────────────────────────────────────────────
@lru_cache
def get_rabbitmq_facade() -> RabbitmqFacade:
    return build_rabbitmq_facade(celery_app)


# ─── Notifier Facade (pub/sub поверх RabbitMQ topic exchange) ───────────────
@lru_cache
def get_notifier_facade() -> NotifierFacade:
    amqp_url = os.environ.get(
        "AMQP_URL",
        os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
    )
    return build_notifier_facade(amqp_url=amqp_url)


# ─── Email Facade ────────────────────────────────────────────────────────────
@lru_cache
def get_email_facade() -> EmailFacade:
    return build_email_facade(
        rabbitmq_facade=get_rabbitmq_facade(),
        smtp_host=os.environ.get("SMTP_HOST", "mailhog"),
        smtp_port=int(os.environ.get("SMTP_PORT", "1025")),
        smtp_from=os.environ.get("SMTP_FROM", "noreply@landing-generator.local"),
    )


# ─── User Facade ─────────────────────────────────────────────────────────────
@lru_cache
def get_user_facade() -> UserFacade:
    return build_user_facade(
        session_factory=SessionLocal,
        email_facade=get_email_facade(),
        jwt_secret=os.environ.get("JWT_SECRET", "dev-secret-change-me"),
        jwt_expires_minutes=int(os.environ.get("JWT_EXPIRES_MINUTES", "30")),
    )


# ─── Generation Facade ───────────────────────────────────────────────────────
@lru_cache
def get_generation_facade() -> GenerationFacade:
    return build_generation_facade(
        session_factory=SessionLocal,
        llm_facade=get_llm_facade(),
        rabbitmq_facade=get_rabbitmq_facade(),
        notifier_facade=get_notifier_facade(),
        default_provider=str(DEFAULT_LLM_PROVIDER),
    )
