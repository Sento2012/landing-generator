# Skill: Code Review

Checklist for reviewing a diff in this repository. Walk through each section and check the changed files against it.

## 1. Layer boundary violations

Run these greps; each should print **nothing** in the diff context:

```bash
# llm/ core must not know about specific providers
grep -rn "from app.llm_openai" backend/app/llm/
grep -rn "from app.llm_anthropic" backend/app/llm/

# provider modules must not know about generation
grep -rn "from app.generation" backend/app/llm_openai/
grep -rn "from app.generation" backend/app/llm_anthropic/

# provider modules must not know about each other
grep -rn "from app.llm_openai" backend/app/llm_anthropic/
grep -rn "from app.llm_anthropic" backend/app/llm_openai/

# only shared/dependency_provider reads env
grep -rn "os.environ" backend/app/ | grep -v "shared/dependency_provider.py" | grep -v "shared/database.py"
```

Any output here is a regression. The composition root is the **only** place that touches `os.environ`.

## 2. Facade is thin

For every change in `domain/facade.py`:

- Each method body is **one or two lines** — get a service from factory, call it, return / proxy events.
- No DB calls. No HTTP. No env reads. No multi-step logic.
- Input is a Transfer DTO. Output is Transfer / `Transfer | None` / `AsyncIterator[Transfer]`.

If a Facade method grew to do real work, the work belongs in `business/` (a new service) and the Facade should delegate.

## 3. Factory only `create_*`

For changes in `domain/factory.py`:

- Methods named `create_*`, returning a fresh service each call.
- No `get_*` lazy-initializing properties.
- No `_build_*` helpers that contain real logic.
- Constructor accepts pre-built dependencies, never raw config (no `api_key` strings — only the already-instantiated `client`).

If you see business logic in Factory, move it to `business/`. If you see lazy initialization or env reads, move them to `dependency_provider.py`.

## 4. DTO discipline at Facade boundary

For every Facade method:

- Argument is a Pydantic model (Transfer), not `int`/`str`/`dict`.
- Return is a Transfer / collection of Transfers / `AsyncIterator[Transfer]`.
- Client DTOs (`*Request`, `*Response`) are NOT used inside `domain/` — they live only in `client/dto/`.

The controller does the mapping `Client DTO ↔ Business Transfer`.

## 5. No magic strings

Scan the diff for string literals that should be enums:

- Status / state values → `StrEnum` in `domain/models/`.
- Event/protocol type names → enum (e.g. `LlmEventType`, `AnthropicChunkType`).
- Tool/function/handler names → enum (e.g. `LlmToolName`).

Bare `"completed"` or `"set_html"` in code is almost always a bug. Compare to the existing enum (`GenerationStatus.COMPLETED`, `LlmToolName.SET_HTML`).

## 6. Captain-obvious docstrings

Remove anything that just restates the name:

- `"""Builds an X."""` on `def build_x()` → delete.
- `"""Returns Y."""` on `def get_y()` → delete.
- Module docstring describing a generic role (`"""Helper module."""`) → delete.

Keep:

- Module docstrings that describe **role in the architecture** (`"""Composition root: ..."""`).
- Comments that explain **why** a decision was made (workarounds, invariants, external constraints).
- Multi-line docstrings that document **state**, edge cases, or non-obvious behavior.

## 7. Tests

For every Facade or HTTP endpoint change:

- A test exists in `backend/tests/` that exercises the public method/route.
- Tests **mock everything below the Facade** (Repository, services, plugins). No real DB, no real LLM.
- HTTP tests use `app.dependency_overrides` to replace the Facade with a `MagicMock`.
- Tests should run in **under a second** total. If they're slow, something I/O leaked through.

Run the suite:

```bash
docker compose exec backend python -m pytest tests/ -v
```

All 27+ tests should be green.

## 8. Adding a new module/provider

If the diff adds a new module, the playbook to verify against is in [`add-module.md`](add-module.md) or [`add-llm-provider.md`](add-llm-provider.md). Check that every step is followed.

## 9. Dependency injection

- Module-level `dependency_provider.py` accepts dependencies as **parameters**, not from env or globals.
- `shared/dependency_provider.py` reads env exactly once at module load (via `os.environ.get`).
- Caching happens via `@lru_cache` on the top-level `get_*_facade()` functions; nowhere else.

## 10. Permission and secrets

- `.gitignore` excludes `.env`. Never commit `.env`.
- `.env.example` contains placeholder values only (no real keys).
- New env vars are documented in `.env.example` AND wired in `docker-compose.yml`.

## 11. Frontend (if changed)

For changes in `frontend/`:

- Imports follow ESM, no CommonJS.
- Types match the backend Client DTO shape (manual sync — there's no codegen yet).
- SSE events handled with explicit `addEventListener("event_name", ...)` (matches backend `event:` lines).
- No business logic in components — keep them rendering-focused.

## 12. Final pass

Before approving:

- [ ] Tests are green.
- [ ] `docker compose up --build` starts without error.
- [ ] At least one manual smoke test of the changed path (POST a generation, watch the stream, see the iframe render).
- [ ] No `.env` files appear in the diff.
- [ ] Imports compile (`docker compose exec backend python -c "import app.main"`).
