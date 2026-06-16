"""HTTP endpoints для аутентификации."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.shared.dependency_provider import get_user_facade
from app.user.client.auth_dependency import CurrentUser
from app.user.client.dto.login_request import LoginRequest
from app.user.client.dto.register_request import RegisterRequest
from app.user.client.dto.token_response import TokenResponse
from app.user.client.dto.user_response import UserResponse
from app.user.domain.business.authentication_service import InvalidCredentialsError
from app.user.domain.business.registration_service import EmailAlreadyTakenError
from app.user.domain.dto.user_create import UserCreateTransfer
from app.user.domain.dto.user_credentials import UserCredentialsTransfer
from app.user.domain.facade import UserFacade

router = APIRouter(prefix="/api/auth", tags=["auth"])

FacadeDep = Annotated[UserFacade, Depends(get_user_facade)]


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, facade: FacadeDep) -> UserResponse:
    try:
        user = await facade.register(UserCreateTransfer(
            email=payload.email,
            password=payload.password,
        ))
    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from None
    return UserResponse.model_validate(user.model_dump())


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, facade: FacadeDep) -> TokenResponse:
    try:
        token = await facade.authenticate(UserCredentialsTransfer(
            email=payload.email,
            password=payload.password,
        ))
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None
    return TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user.model_dump())
