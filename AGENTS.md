# Agent Guide

Document for any AI coding agent working on this repository. Read this before making changes.

## 1. What this project is

**Landing Generator** — a single-page web app where a user enters a text prompt, and an LLM generates a complete HTML/CSS/JS landing page. The user sees streaming progress, then a rendered preview in an iframe. Generations are persisted and reviewable.

**Use case:** portfolio/demo project showcasing layered architecture, LLM tool use, streaming SSE, and Docker-based full-stack development.

## 2. Stack

| Layer | Tech |
| --- | --- |
| Backend | FastAPI, SQLAlchemy 2.0 (async), asyncpg, Pydantic 2 |
| LLM | OpenAI and Anthropic SDKs, streaming with tool/function calling |
| Frontend | React 18, Vite, TypeScript, Tailwind |
| DB | Postgres 16 |
| Orchestration | Docker Compose |
| Tests | pytest + pytest-asyncio |

## 3. Architecture overview

Modular, Spryker-inspired. Each domain concept is a **module** (a top-level Python package under `backend/app/`). Modules talk to each other **only through Facades**.

```
backend/app/
├── main.py                       # FastAPI entry: lifespan, CORS, router registration
├── shared/                       # Cross-cutting infra
│   ├── database.py               # async engine, SessionLocal, Base
│   ├── dependency_provider.py    # composition root (the ONLY place that reads env)
│   └── sse.py                    # generic SSE wrapper for any Pydantic event
│
├── generation/                   # Domain module: generation lifecycle
├── llm/                          # Core: LLM contracts (no concrete providers)
├── llm_openai/                   # Provider module: OpenAI implementation
└── llm_anthropic/                # Provider module: Anthropic implementation
```

### 3.1 Module internal structure

Every domain module follows the same shape (skip subfolders that don't apply):

```
<module>/
├── client/                       # External-facing transport (HTTP / SSE)
│   ├── controller.py             # FastAPI routes
│   └── dto/                      # Request/Response models exposed over HTTP
├── domain/                       # Internal business layer
│   ├── facade.py                 # PUBLIC API of the module
│   ├── factory.py                # Stateless builder of internal services (create_* only)
│   ├── business/                 # Active services (orchestrators, builders)
│   ├── dto/                      # Transfer objects passed between facade/services
│   ├── models/                   # Entities (ORM) + Enums + value objects
│   ├── persistence/              # Repository (READ) + EntityManager (WRITE)
│   └── plugin/                   # Plugin interface and adapters
└── dependency_provider.py        # Module wiring (builds Facade from params)
```

Not every module has all subfolders. For example, `llm/` has no `persistence/` (no DB), `llm_openai/` has no `client/` (no HTTP routes — used internally as a plugin).

## 4. Layer responsibilities

### `client/`

External transport adapter. Knows about HTTP, JSON, SSE. Does **only** two things:

1. Map incoming Client DTO → Business Transfer, call Facade.
2. Map Business Transfer → Client DTO, return.

No business logic, no DB access, no LLM calls.

### `domain/facade.py`

Public API of the module. **Thin** — takes a DTO, asks Factory for the right service, calls it, returns Transfer/iterator. Never has multi-step logic itself.

### `domain/factory.py`

Stateless creator. Constructor receives pre-built dependencies (`client`, `model`, `tools`, `session_factory`, etc.). Methods are **only** `create_*` — they assemble services. No lazy `get_*` caching, no `_build_*` private logic.

### `domain/business/`

Where the actual work happens. Services orchestrating multiple steps (`generator.py` for Generation, `stream_landing_service.py` for LLM providers). Each service does one well-named thing.

### `domain/dto/`

Pydantic models passed between Facade and internal services. **Every Facade method takes and returns DTO** — no bare `int`/`str`/`dict`. Names end in `Transfer` (e.g. `GenerationCreateTransfer`, `LlmPromptTransfer`).

### `domain/models/`

Value objects: ORM entities (SQLAlchemy `Mapped[...]`) and enums (`StrEnum`). Anything immutable that describes shape/state.

### `domain/persistence/`

Data access. CQRS-lite:
- `repository.py` — read operations (`find_by_id`, `list_recent`)
- `entity_manager.py` — write operations (`create`, `mark_running`, `save_result`)

These are the **only** files that import SQLAlchemy directly. They return `Transfer` objects, never raw entities, so domain types don't leak.

### `domain/plugin/`

Extension point. `interface.py` defines the contract; provider modules implement it. Concrete adapters in provider modules (e.g. `llm_openai/domain/plugin/openai_provider_plugin.py`) are **thin** — they delegate to their module's Facade.

### `dependency_provider.py` (per module)

Module wiring. Exposes `build_<module>_facade(deps...) -> Facade` or `build_<module>_plugin(deps...) -> Plugin`. Receives all configuration as parameters. **Never reads env directly.**

### `shared/dependency_provider.py`

Composition root. The **only** place that:
- Reads environment variables.
- Imports every module's wiring function.
- Caches Facades with `@lru_cache` (one instance per app lifetime).
- Exposes FastAPI `Depends()` targets like `get_generation_facade()`.

## 5. Dependency rules

```
shared/dependency_provider.py
        │  reads env, composes everything
        ▼
generation ────────────────► llm ◄──────── llm_openai
                                  ◄──────── llm_anthropic
```

| Module | Can import from |
| --- | --- |
| `generation/` | `llm/domain/*` (contracts only: dto, models, plugin/interface, facade) |
| `llm/` | nothing |
| `llm_openai/` | `llm/domain/*` (contracts only) |
| `llm_anthropic/` | `llm/domain/*` (contracts only) |
| `shared/dependency_provider.py` | everything (this is the composition root) |
| `shared/database.py`, `shared/sse.py` | nothing module-specific |

**Key invariant:** Provider modules (`llm_openai`, `llm_anthropic`) do NOT know about each other and do NOT know about `generation`. `llm/` core does not know about specific providers.

Verify with `grep`:
```bash
grep -rn "from app.llm_openai" backend/app/llm/      # should be empty
grep -rn "from app.llm_anthropic" backend/app/llm/   # should be empty
grep -rn "from app.generation" backend/app/llm*/     # should be empty
```

## 6. Glossary

| Term | Meaning |
| --- | --- |
| **Facade** | The public face of a module. Thin delegator. Every cross-module call goes through a Facade. |
| **Factory** (module) | Builds internal services. Stateless, constructor-injected. Only `create_*` methods. |
| **Transfer** | A Pydantic DTO used internally. Always suffix `Transfer`. |
| **Client DTO** | A Pydantic model for HTTP request/response. Named `*Request`/`*Response`. Separate from Transfers so API can evolve without touching domain. |
| **Plugin** | Concrete implementation of a contract interface from a different module. |
| **Composition root** | `shared/dependency_provider.py`. The only place that reads env, imports concrete providers, and wires everything. |
| **Streaming service** | A service that yields `LlmEventTransfer` events over time (`AsyncIterator[LlmEventTransfer]`). |
| **Tool call** | LLM function-calling protocol. We expose three tools: `set_html`, `set_css`, `set_js`. |
| **Provider** | An LLM vendor (OpenAI, Anthropic). Each has its own module. |

## 7. Conventions

### Naming

| Concept | Pattern | Example |
| --- | --- | --- |
| Module | `snake_case` | `llm_openai` |
| File | `snake_case.py` | `stream_landing_service.py` |
| Class | `PascalCase` | `GenerationFacade`, `OpenAiStreamLandingService` |
| Enum value | `UPPER_SNAKE_CASE` | `LlmEventType.TOOL_START` |
| Function | `snake_case` | `build_openai_plugin`, `apply_tool_content` |
| Internal method | `_leading_underscore` | `_translate_chunks`, `_on_block_start` |

Facades are named `<Module>Facade`. Factories — `<Module>Factory`. Plugins — `<Vendor>ProviderPlugin`.

### Docstrings and comments

Default: **no docstring**. Add one only if the reader can't infer the answer from the name + signature + body.

- **No** captain-obvious docstrings (`"""Returns the user."""` on `get_user()`).
- **Yes** to module-level docstrings that describe the role of the file (used as orientation).
- **Yes** to comments explaining **why** a non-obvious decision was made (workarounds, invariants, external constraints).
- **No** to comments restating what the code does.

### Enums over magic strings

Every set of related string constants is a `StrEnum`. Examples in repo:
- `GenerationStatus` — lifecycle (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`)
- `LlmEventType` — streaming events (`TOOL_START`, `DONE`, ...)
- `LlmProviderName` — provider registry keys (`OPENAI`, `ANTHROPIC`)
- `LlmToolName` — tool identifiers (`SET_HTML`, `SET_CSS`, `SET_JS`)
- `AnthropicChunkType` / `AnthropicBlockType` / `AnthropicDeltaType` — Anthropic protocol

Don't compare to bare strings (`if status == "completed"`). Always go through the enum (`if status == GenerationStatus.COMPLETED`).

### DTO discipline

Every Facade method takes and returns a Pydantic model:

```python
async def create_generation(self, dto: GenerationCreateTransfer) -> GenerationTransfer: ...
async def list_generations(self, dto: GenerationListCriteriaTransfer) -> GenerationListTransfer: ...
async def stream_landing(self, dto: LlmPromptTransfer) -> AsyncIterator[LlmEventTransfer]: ...
```

Internal services (Repository, EntityManager, services in `business/`) may take primitives — they are private to the module.

### Async

The whole backend is async. Use:
- `async def` everywhere on the request path.
- `await` instead of `.then()`/sync wrappers.
- `AsyncSession` / `async_sessionmaker` from SQLAlchemy.
- `AsyncIterator[T]` as the return type for streaming.

For streaming methods, the implementation is an `async def` with `yield` statements (an async generator). Interfaces declare it with `def func(...) -> AsyncIterator[T]` so implementations are free to be sync-returning-iter or async-gen.

### Tests

- Tests live in `backend/tests/`.
- One file per Facade (`test_<module>_facade.py`) + `test_api.py` for HTTP endpoints.
- Tests focus on **public methods only** (Facade methods, HTTP endpoints). Internal services are mocked.
- `pytest.ini` enables `asyncio_mode = auto`, so `async def test_*` functions just work.
- HTTP tests use FastAPI `TestClient` + `app.dependency_overrides` to replace the Facade with a mock.

## 8. How to run

### First time / fresh DB

```bash
cd landing_generator
cp .env.example .env
# Fill in OPENAI_API_KEY (required) and ANTHROPIC_API_KEY (required if provider=anthropic)
docker compose up --build
```

Open <http://localhost:5173>.

### Run tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

### Switch default LLM provider

In `.env`:
```
LLM_PROVIDER=anthropic   # or openai
```

Per-request override: pass `"provider": "anthropic"` in the `POST /api/generations` body.

## 9. Common pitfalls (already encountered in history)

- **Don't import env into modules.** Use `shared/dependency_provider.py` and pass values as parameters.
- **Factory must only `create_*`.** Resist adding `get_*` lazy initializers — wiring belongs in `dependency_provider.py`.
- **Tests skip `lifespan`** by not using `with TestClient(app)`. This avoids needing a live DB.
- **`anthropic` and `openai` SDK version drift.** Newer `httpx` can break older SDKs (`proxies` argument removed). Pin both `httpx` and the SDK in `requirements.txt`.
- **Docker file-permission issue with `__pycache__`.** Files created from inside the container are owned by root. Use `docker compose exec backend chown -R 1000:1000 <path>` when host editing fails.

## 10. Skills

Concrete playbooks for common tasks live in `docs/skills/`:

- [`code-review.md`](docs/skills/code-review.md) — what to look for when reviewing a diff
- [`add-llm-provider.md`](docs/skills/add-llm-provider.md) — adding a new LLM vendor (e.g. DeepSeek, Groq)
- [`add-module.md`](docs/skills/add-module.md) — adding a new domain module (e.g. `user` for auth)

Read the relevant skill before doing the task; the playbook lists every file you need to touch.

## 11. Where to find things fast

| Looking for | File |
| --- | --- |
| HTTP endpoints | `backend/app/generation/client/controller.py` |
| LLM streaming pipeline | `backend/app/llm_*/domain/business/stream_landing_service.py` |
| DB schema | `backend/app/generation/domain/models/entity.py` |
| Wiring / env | `backend/app/shared/dependency_provider.py` |
| Tools/prompt definitions | `backend/app/llm/domain/prompt.py` |
| Tool name routing | `backend/app/llm/domain/business/landing_result_builder.py` |
| Provider switching | `LLM_PROVIDER` env, used in `shared/dependency_provider.py` |
| Frontend state machine | `frontend/src/App.tsx` |

When in doubt about where to add something, ask: *what concept does it belong to?* That answers which module. Then: *what layer?* That answers which subfolder.
