"""Wiring модуля User."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.email.domain.facade import EmailFacade
from app.user.domain.facade import UserFacade
from app.user.domain.factory import UserFactory


def build_user_facade(
    session_factory: async_sessionmaker,
    email_facade: EmailFacade,
    jwt_secret: str,
    jwt_expires_minutes: int,
) -> UserFacade:
    factory = UserFactory(
        session_factory=session_factory,
        email_facade=email_facade,
        jwt_secret=jwt_secret,
        jwt_expires_minutes=jwt_expires_minutes,
    )
    return UserFacade(factory)
