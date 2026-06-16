"""JWT-токен, выдаваемый после логина."""
from pydantic import BaseModel


class JwtTokenTransfer(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int   # секунд до истечения


class JwtPayloadTransfer(BaseModel):
    """Декодированный payload JWT — то, что внутри token'а."""
    user_id: int
    email: str
