"""Composition root приложения.

Единственное место, которое:
- читает env-переменные,
- знает обо ВСЕХ модулях и подключаемых плагинах,
- кеширует собранные Facade (один инстанс на жизнь app),
- отдаёт их FastAPI через Depends().

Сами модули ничего не знают друг про друга — каждый module/dependency_provider.py
билдит только свой собственный stack из переданных параметров.
"""
import os
from functools import lru_cache

from app.generation.dependency_provider import build_generation_facade
from app.generation.domain.facade import GenerationFacade
from app.llm.dependency_provider import build_llm_facade
from app.llm.domain.facade import LlmFacade
from app.llm.domain.models.llm_provider_name import LlmProviderName
from app.llm.domain.prompt import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from app.llm_anthropic.dependency_provider import build_anthropic_plugin
from app.llm_openai.dependency_provider import build_openai_plugin
from app.rabbitmq.dependency_provider import build_rabbitmq_facade
from app.rabbitmq.domain.facade import RabbitmqFacade
from app.shared.database import SessionLocal
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


# ─── Generation Facade ───────────────────────────────────────────────────────
@lru_cache
def get_generation_facade() -> GenerationFacade:
    return build_generation_facade(
        session_factory=SessionLocal,
        llm_facade=get_llm_facade(),
        rabbitmq_facade=get_rabbitmq_facade(),
        default_provider=str(DEFAULT_LLM_PROVIDER),
    )
