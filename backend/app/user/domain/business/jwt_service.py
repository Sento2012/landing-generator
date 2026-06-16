"""JwtService — выдача и валидация JWT access-токенов."""
from datetime import datetime, timedelta, timezone

import jwt

from app.user.domain.dto.jwt_token import JwtPayloadTransfer, JwtTokenTransfer
from app.user.domain.dto.user import UserTransfer


JWT_ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    """Токен не прошёл валидацию (подпись, срок, формат)."""


class JwtService:
    def __init__(self, secret: str, expires_minutes: int) -> None:
        self._secret = secret
        self._expires_minutes = expires_minutes

    def issue(self, user: UserTransfer) -> JwtTokenTransfer:
        now = datetime.now(tz=timezone.utc)
        exp = now + timedelta(minutes=self._expires_minutes)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(payload, self._secret, algorithm=JWT_ALGORITHM)
        return JwtTokenTransfer(
            access_token=token,
            expires_in=self._expires_minutes * 60,
        )

    def decode(self, token: str) -> JwtPayloadTransfer:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[JWT_ALGORITHM])
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(str(e)) from e
        return JwtPayloadTransfer(
            user_id=int(payload["sub"]),
            email=payload["email"],
        )
