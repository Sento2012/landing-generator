# Skill: Add a new domain module

Use this when you need a new business concept that isn't a generation or an LLM provider. Examples: `user` (auth), `template` (saved prompts), `analytics` (usage events), `billing` (subscriptions).

We'll use **`user`** as the example throughout — adding user accounts with email/password.

## 0. Decide what you actually need

Before scaffolding, answer:

1. **What concept does this module own?** (One sentence.)
2. **Does it need persistence?** If yes → there will be a `persistence/` subfolder.
3. **Does it need HTTP endpoints?** If yes → there will be a `client/` subfolder.
4. **Does it need to call other modules?** Which Facades?
5. **Does anyone need to call it?** Through which Facade method?

For `user`:

1. User identity — registration, login, current-user lookup.
2. Yes (users table).
3. Yes (`POST /api/users/register`, `POST /api/users/login`, `GET /api/users/me`).
4. None directly.
5. Eventually `generation` would call `UserFacade.get_by_token()` to attach a user to a generation.

## 1. Scaffold the folders

```bash
mkdir -p backend/app/user/client/dto
mkdir -p backend/app/user/domain/business
mkdir -p backend/app/user/domain/dto
mkdir -p backend/app/user/domain/models
mkdir -p backend/app/user/domain/persistence
touch backend/app/user/__init__.py
touch backend/app/user/client/__init__.py
touch backend/app/user/client/dto/__init__.py
touch backend/app/user/domain/__init__.py
touch backend/app/user/domain/business/__init__.py
touch backend/app/user/domain/dto/__init__.py
touch backend/app/user/domain/models/__init__.py
touch backend/app/user/domain/persistence/__init__.py
```

End shape:

```
user/
├── __init__.py
├── client/
│   ├── controller.py
│   └── dto/
│       ├── login_request.py
│       ├── register_request.py
│       └── user_response.py
├── dependency_provider.py
└── domain/
    ├── facade.py
    ├── factory.py
    ├── business/
    │   └── password_hasher.py        # e.g. wrapping bcrypt
    ├── dto/
    │   ├── user.py
    │   ├── user_create.py
    │   └── user_credentials.py
    ├── models/
    │   ├── entity.py                 # ORM
    │   └── user_role.py              # enum, if needed
    └── persistence/
        ├── entity_manager.py
        └── repository.py
```

## 2. Models (entity + enums)

`backend/app/user/domain/models/entity.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

Register the entity in `backend/app/main.py` so SQLAlchemy sees it at startup:

```diff
  from app.generation.domain.models import entity  # noqa: F401
+ from app.user.domain.models import entity as _user_entity  # noqa: F401
```

(Or rename to avoid the shadowing — `as _user_entity` is fine.)

Enums (if any) live in `models/` alongside.

## 3. DTOs (Transfer)

`backend/app/user/domain/dto/user.py`:

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserTransfer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime
```

`backend/app/user/domain/dto/user_create.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class UserCreateTransfer(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
```

`backend/app/user/domain/dto/user_credentials.py` — for login input.

## 4. Persistence (Repository + EntityManager)

`backend/app/user/domain/persistence/repository.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.user.domain.dto.user import UserTransfer
from app.user.domain.models.entity import UserEntity


class UserRepository:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, user_id: int) -> UserTransfer | None:
        async with self._session_factory() as session:
            entity = await session.get(UserEntity, user_id)
            return UserTransfer.model_validate(entity) if entity else None

    async def find_by_email(self, email: str) -> UserEntity | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.email == email)
            )
            return result.scalar_one_or_none()
```

Note: `find_by_email` returns the **entity** because the caller needs the `password_hash` for verification — that field isn't on the public `UserTransfer`. This is the rare case where it's fine to return an entity, since the consumer is inside the module (the password-check service in `business/`).

`backend/app/user/domain/persistence/entity_manager.py`: `create`, `update_password`, etc. — write operations.

## 5. Business services

`backend/app/user/domain/business/password_hasher.py`:

```python
import bcrypt


class PasswordHasher:
    def hash(self, plaintext: str) -> str:
        return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()

    def verify(self, plaintext: str, hashed: str) -> bool:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
```

Add other services as needed (`JwtIssuer`, `LoginService`, ...).

## 6. Factory

`backend/app/user/domain/factory.py`:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.user.domain.business.password_hasher import PasswordHasher
from app.user.domain.persistence.entity_manager import UserEntityManager
from app.user.domain.persistence.repository import UserRepository


class UserFactory:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    def create_repository(self) -> UserRepository:
        return UserRepository(self._session_factory)

    def create_entity_manager(self) -> UserEntityManager:
        return UserEntityManager(self._session_factory)

    def create_password_hasher(self) -> PasswordHasher:
        return PasswordHasher()
```

Only `create_*`. Pre-built dependencies in `__init__`.

## 7. Facade

`backend/app/user/domain/facade.py`:

```python
from app.user.domain.dto.user import UserTransfer
from app.user.domain.dto.user_create import UserCreateTransfer
from app.user.domain.dto.user_credentials import UserCredentialsTransfer
from app.user.domain.factory import UserFactory


class UserFacade:
    def __init__(self, factory: UserFactory) -> None:
        self._factory = factory

    async def register(self, dto: UserCreateTransfer) -> UserTransfer:
        hasher = self._factory.create_password_hasher()
        em = self._factory.create_entity_manager()
        return await em.create(dto, hasher.hash(dto.password))

    async def authenticate(self, dto: UserCredentialsTransfer) -> UserTransfer | None:
        repo = self._factory.create_repository()
        hasher = self._factory.create_password_hasher()
        # ... small orchestration: lookup user by email, verify password
```

Thin. Multi-step orchestrations like "find user → verify password → mint JWT" should ideally live in a `business/login_service.py` so the Facade is a 1-line delegate. Pick whichever keeps the Facade method to 1–3 lines.

## 8. Module dependency_provider

`backend/app/user/dependency_provider.py`:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.user.domain.facade import UserFacade
from app.user.domain.factory import UserFactory


def build_user_facade(session_factory: async_sessionmaker) -> UserFacade:
    factory = UserFactory(session_factory=session_factory)
    return UserFacade(factory)
```

Parameters only. No env. No globals.

## 9. Client DTOs

`backend/app/user/client/dto/register_request.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
```

Same for `login_request.py`, `user_response.py`. Keep them separate from domain Transfers even if fields are identical — they evolve independently.

## 10. Controller

`backend/app/user/client/controller.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.shared.dependency_provider import get_user_facade
from app.user.client.dto.register_request import RegisterRequest
from app.user.client.dto.user_response import UserResponse
from app.user.domain.dto.user_create import UserCreateTransfer
from app.user.domain.facade import UserFacade

router = APIRouter(prefix="/api/users", tags=["users"])

FacadeDep = Annotated[UserFacade, Depends(get_user_facade)]


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, facade: FacadeDep) -> UserResponse:
    business_dto = UserCreateTransfer(email=payload.email, password=payload.password)
    result = await facade.register(business_dto)
    return UserResponse.model_validate(result.model_dump())
```

Controller only maps Client DTO ↔ Business Transfer and delegates. Nothing else.

## 11. Wire into composition root

`backend/app/shared/dependency_provider.py`:

```diff
+ from app.user.dependency_provider import build_user_facade
+ from app.user.domain.facade import UserFacade

  ...

+ @lru_cache
+ def get_user_facade() -> UserFacade:
+     return build_user_facade(session_factory=SessionLocal)
```

## 12. Register router

`backend/app/main.py`:

```diff
+ from app.user.client.controller import router as user_router
  ...
  app.include_router(generation_router)
+ app.include_router(user_router)
```

## 13. Reset the DB (no migrations yet)

The new `users` table won't appear without a fresh `create_all`. Easiest:

```bash
docker compose down -v   # drops the pgdata volume
docker compose up --build
```

For production, this would be an Alembic migration. We don't have Alembic configured yet (intentional — see README).

## 14. Tests

Add `backend/tests/test_user_facade.py` mirroring `test_generation_facade.py`. Test only the public Facade methods, mock Factory + sub-services.

Add user-route tests to `backend/tests/test_api.py` (or create `test_user_api.py`) using `app.dependency_overrides[get_user_facade]`.

## 15. Smoke test

```bash
docker compose up --build
docker compose exec backend python -m pytest tests/ -v
curl -X POST localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"a@b.c","password":"hunter222!"}'
```

## 16. Common mistakes

- **Mixing `client/dto` and `domain/dto`.** They're different by design. Even if the fields are identical today, keep two copies; the boundary lets API and domain evolve independently.
- **Skipping the entity registration in `main.py`.** Tables created by `Base.metadata.create_all` are only those whose entity has been imported. Forget the `noqa: F401` line and your table won't exist.
- **Importing across module boundaries without going through Facade.** If `generation/` needs the current user, it should receive `UserFacade` via its `BusinessFactory` constructor (from `shared/dependency_provider.py`). Do **not** import `UserRepository` directly.
- **Putting orchestrations in Facade.** If a method does more than ~3 steps, extract a service in `business/`.
- **Forgetting to remove captain-obvious docstrings.** Skim the new files; any `"""Hashes the password."""` on `def hash_password()` should be deleted.

## 17. After landing the module

Update `AGENTS.md` § 5 to include the new module in the dependency-rules table.
