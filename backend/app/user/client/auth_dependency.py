"""FastAPI dependency `current_user` — извлекает юзера из JWT в Authorization header."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.shared.dependency_provider import get_user_facade
from app.user.domain.business.jwt_service import InvalidTokenError
from app.user.domain.dto.user import UserTransfer
from app.user.domain.facade import UserFacade

# tokenUrl только для Swagger UI кнопки Authorize.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    facade: Annotated[UserFacade, Depends(get_user_facade)],
) -> UserTransfer:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    try:
        payload = facade.decode_token(token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        ) from e

    user = await facade.get_user_by_id(payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


CurrentUser = Annotated[UserTransfer, Depends(get_current_user)]
