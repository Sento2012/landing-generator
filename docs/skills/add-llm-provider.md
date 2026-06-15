# Skill: Add a new LLM provider

This is the most common extension point. Use it when you want to add a vendor (e.g. DeepSeek, Groq, Mistral, a local Ollama, etc.).

The new provider is a **separate top-level module** under `backend/app/`. It implements the existing `LlmProviderPluginInterface` and is registered in `shared/dependency_provider.py`.

We'll use **DeepSeek** as the example. Replace `deepseek` / `DeepSeek` with your vendor name everywhere.

## 0. Prerequisites

- The vendor offers an HTTP API with streaming and either function-calling or a similar tool-use mechanism. (Pure text completion is workable but less clean.)
- A Python SDK exists for it. If not, you'll need to call the HTTP API directly with `httpx`.
- You know what their streaming protocol looks like (chunk shape, end-of-stream signal).

## 1. Add the SDK to requirements

`backend/requirements.txt`:

```diff
+ deepseek-sdk==X.Y.Z
```

Pin the version. After this, rebuild the image: `docker compose build backend`.

## 2. Register the provider name in the enum

`backend/app/llm/domain/models/llm_provider_name.py`:

```python
class LlmProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"   # ← new
```

## 3. Create the module skeleton

```bash
mkdir -p backend/app/llm_deepseek/domain/business
mkdir -p backend/app/llm_deepseek/domain/plugin
# Add models/ only if the vendor's protocol has enum-worthy constants
# mkdir -p backend/app/llm_deepseek/domain/models
touch backend/app/llm_deepseek/__init__.py
touch backend/app/llm_deepseek/domain/__init__.py
touch backend/app/llm_deepseek/domain/business/__init__.py
touch backend/app/llm_deepseek/domain/plugin/__init__.py
```

End shape:

```
llm_deepseek/
├── __init__.py
├── dependency_provider.py
└── domain/
    ├── __init__.py
    ├── facade.py
    ├── factory.py
    ├── business/
    │   ├── stream_landing_service.py
    │   └── tools_schema.py
    └── plugin/
        └── deepseek_provider_plugin.py
```

(Plus `models/<vendor>_chunk_event_types.py` if the chunk protocol has enum-worthy constants.)

## 4. Implement `tools_schema.py`

`backend/app/llm_deepseek/domain/business/tools_schema.py`:

```python
from app.llm.domain.models.tool_name import LlmToolName


def build_deepseek_tools_schema(
    tool_descriptions: dict[LlmToolName, dict[str, str]],
) -> list[dict]:
    # Adapt the common TOOL_DESCRIPTIONS dict to whatever shape DeepSeek wants.
    # For OpenAI-compatible APIs this is identical to build_openai_tools_schema.
    return [...]
```

## 5. Implement `stream_landing_service.py`

Mirror the existing implementations (`llm_openai/domain/business/stream_landing_service.py` or `llm_anthropic/domain/business/stream_landing_service.py`). Pick whichever protocol is closer.

Required public surface:

```python
class DeepSeekStreamLandingService:
    def __init__(
        self,
        client: ...,        # the vendor's async HTTP client
        model: str,
        tools: list[dict],
        system_prompt: str,
    ) -> None: ...

    async def stream(self, dto: LlmPromptTransfer) -> AsyncIterator[LlmEventTransfer]:
        ...
```

Implementation contract:

- Yield `LlmEventTransfer` events with `LlmEventType` values: `TOOL_START`, `TOOL_DELTA` (optional), `TOOL_COMPLETE`, `DONE` (with a populated `LandingResultTransfer`), or `ERROR`.
- Reuse `apply_tool_content()` from `app.llm.domain.business.landing_result_builder` to route tool content into `result.html` / `result.css` / `result.js`.
- Decompose the method: `stream()` orchestrates, `_translate_chunks()` does the loop, `_extract_landing_result()` builds the final transfer. See Anthropic for a cleaner pattern.
- Wrap vendor exceptions and yield `ERROR` events; never let a raw exception escape.

## 6. Implement `factory.py`

`backend/app/llm_deepseek/domain/factory.py`:

```python
from <vendor_sdk> import AsyncClient

from app.llm_deepseek.domain.business.stream_landing_service import (
    DeepSeekStreamLandingService,
)


class DeepSeekFactory:
    def __init__(
        self,
        client: AsyncClient,
        model: str,
        tools: list[dict],
        system_prompt: str,
    ) -> None:
        self._client = client
        self._model = model
        self._tools = tools
        self._system_prompt = system_prompt

    def create_stream_landing_service(self) -> DeepSeekStreamLandingService:
        return DeepSeekStreamLandingService(
            client=self._client,
            model=self._model,
            tools=self._tools,
            system_prompt=self._system_prompt,
        )
```

Only `create_*` methods. No `get_client()`, no `_build_tools()`, no lazy init. All inputs are pre-built and injected.

## 7. Implement `facade.py`

`backend/app/llm_deepseek/domain/facade.py`:

```python
from typing import AsyncIterator

from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm_deepseek.domain.factory import DeepSeekFactory


class DeepSeekFacade:
    def __init__(self, factory: DeepSeekFactory) -> None:
        self._factory = factory

    async def stream_landing(
        self,
        dto: LlmPromptTransfer,
    ) -> AsyncIterator[LlmEventTransfer]:
        service = self._factory.create_stream_landing_service()
        async for event in service.stream(dto):
            yield event
```

## 8. Implement the plugin

`backend/app/llm_deepseek/domain/plugin/deepseek_provider_plugin.py`:

```python
from typing import AsyncIterator

from app.llm.domain.dto.llm_event import LlmEventTransfer
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm.domain.plugin.interface import LlmProviderPluginInterface
from app.llm_deepseek.domain.facade import DeepSeekFacade


class DeepSeekProviderPlugin(LlmProviderPluginInterface):
    def __init__(self, facade: DeepSeekFacade) -> None:
        self._facade = facade

    async def stream_landing(
        self,
        prompt: str,
    ) -> AsyncIterator[LlmEventTransfer]:
        async for event in self._facade.stream_landing(LlmPromptTransfer(prompt=prompt)):
            yield event
```

Thin adapter. The plugin interface takes `str`; we wrap it into our internal DTO and delegate.

## 9. Implement `dependency_provider.py`

`backend/app/llm_deepseek/dependency_provider.py`:

```python
from <vendor_sdk> import AsyncClient

from app.llm.domain.models.tool_name import LlmToolName
from app.llm_deepseek.domain.business.tools_schema import build_deepseek_tools_schema
from app.llm_deepseek.domain.facade import DeepSeekFacade
from app.llm_deepseek.domain.factory import DeepSeekFactory
from app.llm_deepseek.domain.plugin.deepseek_provider_plugin import (
    DeepSeekProviderPlugin,
)


def build_deepseek_plugin(
    api_key: str,
    model: str,
    system_prompt: str,
    tool_descriptions: dict[LlmToolName, dict[str, str]],
) -> DeepSeekProviderPlugin:
    client = AsyncClient(api_key=api_key)
    tools = build_deepseek_tools_schema(tool_descriptions)
    factory = DeepSeekFactory(
        client=client,
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
    return DeepSeekProviderPlugin(DeepSeekFacade(factory))
```

This file is the only place in your new module that imports the vendor SDK directly (other than the service that uses the client).

## 10. Wire it into the composition root

`backend/app/shared/dependency_provider.py`:

```diff
+ from app.llm_deepseek.dependency_provider import build_deepseek_plugin

  @lru_cache
  def get_llm_facade() -> LlmFacade:
      plugins = {
          LlmProviderName.OPENAI: build_openai_plugin(
              api_key=os.environ["OPENAI_API_KEY"],
              model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
              system_prompt=SYSTEM_PROMPT,
              tool_descriptions=TOOL_DESCRIPTIONS,
          ),
          LlmProviderName.ANTHROPIC: build_anthropic_plugin(...),
+         LlmProviderName.DEEPSEEK: build_deepseek_plugin(
+             api_key=os.environ["DEEPSEEK_API_KEY"],
+             model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
+             system_prompt=SYSTEM_PROMPT,
+             tool_descriptions=TOOL_DESCRIPTIONS,
+         ),
      }
      return build_llm_facade(plugins=plugins, default=DEFAULT_LLM_PROVIDER)
```

## 11. Update env

`.env.example`:

```diff
+ DEEPSEEK_API_KEY=...
+ DEEPSEEK_MODEL=deepseek-chat
```

`docker-compose.yml` → `backend.environment`:

```diff
+ DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:-}
+ DEEPSEEK_MODEL: ${DEEPSEEK_MODEL:-deepseek-chat}
```

## 12. Add a Facade test

`backend/tests/test_llm_deepseek_facade.py` — copy from `test_llm_openai_facade.py` and rename. The test only checks that `DeepSeekFacade.stream_landing` delegates to its service with the DTO and proxies events. **Do not** test the streaming logic itself here — that's an internal-service concern.

## 13. Smoke test

```bash
docker compose up --build
docker compose exec backend python -m pytest tests/ -v   # all green
curl -X POST localhost:8000/api/generations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a landing about coffee","provider":"deepseek"}'
# then GET /api/generations/<id>/stream and watch the SSE
```

## 14. Common mistakes

- **Importing from another provider module.** Each provider stands alone. If you find yourself doing `from app.llm_openai...` in `llm_deepseek/`, stop and lift the shared code into `llm/domain/business/` instead.
- **Putting logic in Factory.** If you wrote `_build_*` or `get_*` methods in the Factory, move them to `business/` or to `dependency_provider.py`.
- **Reading env inside the module.** Only `shared/dependency_provider.py` reads env. The module receives `api_key`, `model`, `system_prompt`, `tool_descriptions` as parameters.
- **Forgetting the enum entry.** If `LlmProviderName.DEEPSEEK` doesn't exist, the dict-keyed plugin registry won't match and `LlmPluginResolver` will raise on first use.
- **Not pinning vendor SDK + transitive deps.** SDKs that depend on `httpx` can break on a new `httpx` release (we've already been bitten). Pin both.

## 15. Optional cleanups

- If the vendor's protocol has enum-worthy chunk/event types (like Anthropic does), put them in `llm_deepseek/domain/models/<vendor>_chunk_event_types.py` and use them in the service instead of bare strings.
- If you're tempted to fan out `stream()` into many helpers, follow the Anthropic decomposition: `_open_stream` / `_translate_chunks` / `_on_*` per chunk type / `_extract_landing_result`.
