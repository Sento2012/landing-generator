# Landing Generator

Web-приложение, генерирующее одностраничные лендинги по текстовому промпту через LLM.
Spryker-inspired слоистая архитектура на Python, multi-tenant LLM провайдеры (OpenAI/Anthropic),
фоновая обработка через Celery + RabbitMQ.

## Стек

| Слой | Что |
| --- | --- |
| **Backend** | FastAPI · SQLAlchemy 2.0 async · asyncpg · Pydantic 2 · Alembic |
| **LLM** | OpenAI SDK · Anthropic SDK · streaming с tool/function calling |
| **Task queue** | Celery · RabbitMQ broker |
| **Frontend** | React 18 · Vite · TypeScript · Tailwind |
| **DB** | Postgres 16 |
| **Orchestration** | Docker Compose |
| **Tests** | pytest · pytest-asyncio (29 тестов, <1s прогон) |

## Архитектура — кратко

```
backend/
├── app/
│   ├── main.py                       # FastAPI entry
│   ├── shared/                       # cross-module: DB, SSE, composition root
│   ├── generation/                   # домен: lifecycle генераций (HTTP API + business)
│   ├── llm/                          # ядро LLM (контракт + plugin interface)
│   ├── llm_openai/                   # plugin: OpenAI implementation
│   ├── llm_anthropic/                # plugin: Anthropic implementation
│   └── rabbitmq/                     # generic task publisher (Celery send_task wrapper)
└── worker/                           # Celery worker entry points
    ├── celery_app.py
    └── generation_task.py
```

Каждый модуль внутри:

```
<module>/
├── client/                           # HTTP entry point + Request/Response DTO
├── dependency_provider.py            # wiring (принимает зависимости параметрами)
└── domain/
    ├── facade.py                     # public API модуля (тонкий, только делегация)
    ├── factory.py                    # сборщик сервисов (только create_*)
    ├── business/                     # services / orchestrators
    ├── dto/                          # Pydantic Transfer объекты
    ├── models/                       # ORM entities + enums
    ├── persistence/                  # Repository + EntityManager
    └── plugin/                       # plugin interface / adapter
```

**Inter-module communication только через Facade.** Composition root —
[`app/shared/dependency_provider.py`](backend/app/shared/dependency_provider.py) — единственное
место, читающее env и собирающее всё вместе.

Подробное описание архитектуры, конвенций и точек расширения — в [AGENTS.md](AGENTS.md).
Playbook'и для типичных задач — в [docs/skills/](docs/skills/).

## Поток одной генерации

```
[Client]                  [Backend API]              [RabbitMQ]            [Celery Worker]
   │                           │                        │                         │
   ├─ POST /generations ──────►│ create record (pending) │                         │
   │                           │ rabbitmq.publish_task ─►│                         │
   │  ◄─ 201 + id ─────────────│                         ├── Task message ────────►│
   │                                                                  GenerationExecutor.execute:
   │                                                                  - mark_running
   │                                                                  - call OpenAI/Anthropic (streaming)
   │                                                                  - save html/css/js
   │                                                                  - mark completed
   │
   ├─ GET /:id/stream ───────►│ Generator.stream (polls БД)
   │  (SSE)                    │
   │  ◄─ SSE: tool_start ──────│ (когда status = running)
   │  ◄─ SSE: done + result ───│ (когда status = completed)
```

Backend отвечает 201 за миллисекунды (запись в БД + публикация message). LLM-генерация
(7-30 секунд) — отдельный worker-процесс, переживает рестарт клиента и закрытие вкладки.

## Multi-tenant LLM

Per-request выбор провайдера через тело запроса:

```bash
curl -X POST localhost:8000/api/generations \
  -d '{"prompt": "landing about coffee", "provider": "anthropic"}'
```

`provider` сохраняется на записи генерации (часть её identity), используется и при первом
запуске, и при последующих replay'ах.

Default — `LLM_PROVIDER` из `.env`. Добавление нового провайдера — отдельный модуль
`llm_<vendor>/` + одна строка в composition root, никакие другие модули не трогаем
(см. [docs/skills/add-llm-provider.md](docs/skills/add-llm-provider.md)).

## Запуск

```bash
cd landing_generator
cp .env.example .env
# Вписать OPENAI_API_KEY (обязательно) и ANTHROPIC_API_KEY (если используется)
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (Swagger на `/docs`)
- RabbitMQ management UI: http://localhost:15672 (guest/guest)
- Postgres: localhost:5432

Запуск работает через `migrate` → `backend` + `celery_worker`:
- `migrate` запускает `alembic upgrade head` и завершается.
- `backend` стартует только после `service_completed_successfully` от `migrate`.

## Тесты

```bash
docker compose exec backend python -m pytest tests/ -v
```

29 тестов на public API всех Facade'ов и HTTP endpoint'ов. Все мокаются ниже Facade —
ни реальный LLM, ни реальный broker, ни реальная БД не нужны. Прогон ~0.7s.

## Что специально не сделано

- **Per-token SSE streaming.** Сейчас события идут через polling БД (раз в 0.5s). Для
  fine-grained стрима (TOOL_DELTA per character как у ChatGPT) нужен Redis pub/sub
  канал на `gen_id` между worker и SSE endpoint. Описано в `AGENTS.md`.
- **Auth.** API открыт. Скилл для добавления — [docs/skills/add-module.md](docs/skills/add-module.md)
  показывает паттерн на примере `user`-модуля.
- **Observability.** Нет structured logging, метрик, tracing — нужны для прода.
- **CI.** Нет GitHub Actions workflow — был бы один из самых дешёвых wins.

## Что внутри для собеседования

- **Layered architecture** на Python — нечастая вещь, обычно встречается в PHP/Java мире.
- **Plugin pattern** для LLM с чистым swap'ом провайдера через composition root.
- **DTO discipline** на каждой границе: client DTO ↔ business Transfer.
- **Celery + RabbitMQ** для фоновой обработки, sync↔async bridge через `asyncio.run`.
- **Alembic** с async-config, отдельный `migrate` сервис в compose.
- **Streaming с tool use** — нетривиальная унификация OpenAI и Anthropic streaming-протоколов.
- **Тесты** только на public API, всё внутреннее замокано — быстрые и устойчивые к рефакторингу.
- **Composition root** как единственная точка чтения env.

## Структура полностью

```
landing_generator/
├── AGENTS.md                         # Agent guide (любой AI-агент)
├── README.md                         # этот файл
├── docker-compose.yml
├── .env.example
├── docs/skills/
│   ├── code-review.md
│   ├── add-llm-provider.md
│   └── add-module.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── shared/
│   │   ├── generation/
│   │   ├── llm/
│   │   ├── llm_openai/
│   │   ├── llm_anthropic/
│   │   └── rabbitmq/
│   ├── worker/
│   │   ├── celery_app.py
│   │   └── generation_task.py
│   └── tests/
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        └── App.tsx
```
