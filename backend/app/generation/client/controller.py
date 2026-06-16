"""HTTP endpoints для Generation модуля.

Все endpoint'ы protected — требуют JWT в Authorization header.
user_id берётся из current_user (не из body / query), что предотвращает
подделку через сетевой запрос.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.generation.client.dto.create_generation_request import CreateGenerationRequest
from app.generation.client.dto.generation_list_response import GenerationListResponse
from app.generation.client.dto.generation_response import GenerationResponse
from app.generation.domain.facade import GenerationFacade
from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.dto.generation_list_criteria import (
    GenerationListCriteriaTransfer,
)
from app.shared.dependency_provider import get_generation_facade
from app.shared.sse import stream_as_sse
from app.user.client.auth_dependency import CurrentUser

router = APIRouter(prefix="/api/generations", tags=["generations"])

FacadeDep = Annotated[GenerationFacade, Depends(get_generation_facade)]


@router.post("", response_model=GenerationResponse, status_code=201)
async def create_generation(
    payload: CreateGenerationRequest,
    current_user: CurrentUser,
    facade: FacadeDep,
) -> GenerationResponse:
    business_dto = GenerationCreateTransfer(
        prompt=payload.prompt,
        provider=payload.provider,
        user_id=current_user.id,
    )
    result = await facade.create_generation(business_dto)
    return GenerationResponse.model_validate(result.model_dump())


@router.get("", response_model=GenerationListResponse)
async def list_generations(
    current_user: CurrentUser,
    facade: FacadeDep,
    limit: int = 50,
) -> GenerationListResponse:
    business_dto = GenerationListCriteriaTransfer(
        user_id=current_user.id,
        limit=limit,
    )
    result = await facade.list_generations(business_dto)
    return GenerationListResponse.model_validate(result.model_dump())


@router.get("/{gen_id}", response_model=GenerationResponse)
async def get_generation(
    gen_id: int,
    current_user: CurrentUser,
    facade: FacadeDep,
) -> GenerationResponse:
    result = await facade.get_generation(
        GenerationByIdTransfer(id=gen_id, user_id=current_user.id)
    )
    if result is None:
        raise HTTPException(404, "Generation not found")
    return GenerationResponse.model_validate(result.model_dump())


@router.get("/{gen_id}/stream")
async def stream_generation(
    gen_id: int,
    current_user: CurrentUser,
    facade: FacadeDep,
) -> StreamingResponse:
    return stream_as_sse(facade.stream_generation(
        GenerationByIdTransfer(id=gen_id, user_id=current_user.id)
    ))
