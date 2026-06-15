"""HTTP endpoints для Generation модуля.

Контроллер делает ДВЕ вещи и больше ничего:
1. Маппит входящие Client DTO → Business Transfer и зовёт Facade.
2. Маппит исходящий Business Transfer → Client DTO и отдаёт.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.generation.domain.facade import GenerationFacade
from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.dto.generation_list_criteria import (
    GenerationListCriteriaTransfer,
)
from app.generation.client.dto.create_generation_request import CreateGenerationRequest
from app.generation.client.dto.generation_list_response import GenerationListResponse
from app.generation.client.dto.generation_response import GenerationResponse
from app.shared.dependency_provider import get_generation_facade
from app.shared.sse import stream_as_sse

router = APIRouter(prefix="/api/generations", tags=["generations"])

FacadeDep = Annotated[GenerationFacade, Depends(get_generation_facade)]


# ─── Create ──────────────────────────────────────────────────────────────────
@router.post("", response_model=GenerationResponse, status_code=201)
async def create_generation(
    payload: CreateGenerationRequest,
    facade: FacadeDep,
) -> GenerationResponse:
    business_dto = GenerationCreateTransfer(
        prompt=payload.prompt,
        provider=payload.provider,
    )
    result = await facade.create_generation(business_dto)
    return GenerationResponse.model_validate(result.model_dump())


# ─── List ────────────────────────────────────────────────────────────────────
@router.get("", response_model=GenerationListResponse)
async def list_generations(
    facade: FacadeDep,
    limit: int = 50,
) -> GenerationListResponse:
    business_dto = GenerationListCriteriaTransfer(limit=limit)
    result = await facade.list_generations(business_dto)
    return GenerationListResponse.model_validate(result.model_dump())


# ─── Get by id ───────────────────────────────────────────────────────────────
@router.get("/{gen_id}", response_model=GenerationResponse)
async def get_generation(gen_id: int, facade: FacadeDep) -> GenerationResponse:
    result = await facade.get_generation(GenerationByIdTransfer(id=gen_id))
    if result is None:
        raise HTTPException(404, "Generation not found")
    return GenerationResponse.model_validate(result.model_dump())


# ─── Stream ──────────────────────────────────────────────────────────────────
@router.get("/{gen_id}/stream")
async def stream_generation(gen_id: int, facade: FacadeDep) -> StreamingResponse:
    return stream_as_sse(facade.stream_generation(GenerationByIdTransfer(id=gen_id)))
