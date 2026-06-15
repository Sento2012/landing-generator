# Landing Generator

LLM-приложение для генерации одностраничных лендингов по текстовому промпту.
Стек: **FastAPI + Postgres + React + Tailwind**, всё в Docker. LLM —
**Anthropic Claude Sonnet 4.6** с **tool use** (3 инструмента: `set_html`,
`set_css`, `set_js`), стриминг через **SSE**.

## Архитектура

```
┌──────────────┐   POST /api/generations
│              │ ─────────────────────────►  ┌──────────────┐
│   React +    │                              │   FastAPI    │
│   Tailwind   │   SSE /generations/:id      │              │
│  (Vite dev)  │ ◄─────────────────────────  │   + Claude   │
│              │                              │   streaming  │
└──────────────┘                              └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  Postgres    │
                                              │ (история)    │
                                              └──────────────┘
```

**Flow одной генерации:**
1. Юзер вводит промпт, фронт делает `POST /api/generations` → получает `id`.
2. Фронт открывает `EventSource('/api/generations/:id/stream')`.
3. Бэкенд при подключении SSE запускает Claude в режиме streaming с tools.
4. Каждый tool call (`set_html`, `set_css`, `set_js`) превращается в SSE-событие
   → фронт показывает шаг в лоадере.
5. По завершению — событие `done` с финальным html/css/js, бэкенд сохраняет в БД.
6. Фронт рендерит результат в `<iframe srcDoc=...>`.

## Запуск

```bash
cd landing_generator
cp .env.example .env
# Вписать в .env свой ANTHROPIC_API_KEY (https://console.anthropic.com/)

docker compose up --build
```

- Фронтенд: http://localhost:5173
- Бэкенд:   http://localhost:8000  (Swagger: /docs)
- Postgres: localhost:5432

## Что показывает (для резюме)

- **LLM с tool use** — нетривиальный паттерн (не «модель отдала markdown, мы парсим»),
  а строгий tool-calling протокол. Каждый тул кладёт свой кусок в результат.
- **Streaming SSE** — события прилетают на фронт по мере генерации. Лоадер
  не «крутится в пустоту», а отражает реальный прогресс.
- **Полный стек в Docker** — Postgres + Python + React, всё запускается одной командой.
- **Async везде** — FastAPI + asyncpg + Anthropic async SDK + asyncio.

## Структура

```
landing_generator/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── database.py    # async SQLAlchemy + asyncpg
│       ├── models.py      # ORM модели
│       ├── schemas.py     # Pydantic DTO
│       ├── llm.py         # Anthropic streaming с tools
│       └── main.py        # FastAPI endpoints + SSE
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        └── index.css
```

## Что не сделано (что можно докрутить для resume-плюсов)

- Регенерация и итеративные правки («сделай заголовок больше»).
- Экспорт в zip с готовыми файлами.
- Кэширование system prompt в Anthropic API (есть в коде, можно докрутить).
- Auth (сейчас все генерации публичные).
- Rate limiting (Anthropic дорогой).
- Если SSE-соединение оборвалось — генерация прерывается. В проде вынес бы
  в фоновый воркер с in-process pub/sub или Redis.
