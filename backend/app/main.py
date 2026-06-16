"""FastAPI приложение — точка входа. Подключает роутеры модулей и lifespan."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.generation.client.controller import router as generation_router
from app.shared.database import engine
from app.user.client.controller import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="Landing Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generation_router)
app.include_router(auth_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
