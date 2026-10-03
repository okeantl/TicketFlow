from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_access_token, hash_password, verify_password
from src.models import User
from src.modules.auth.schemas import UserLogin, UserRegister


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, data: UserRegister) -> User | None:
        result = await self.db.execute(select(User).where(User.email == data.email))
        email = result.scalars().first()
        if email is not None:
            return None
        else:
            user = User(email=data.email, hashed_password=hash_password(data.password))
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user

    async def login(self, data: UserLogin) -> str | None:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalars().first()
        if user is None:
            return None
        if not verify_password(data.password, user.hashed_password):
            return None
        return create_access_token(user.id)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    return AuthService(db)
