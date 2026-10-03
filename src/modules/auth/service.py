from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from src.core.security import create_access_token, hash_password, verify_password
from src.models import User
from src.modules.auth.schemas import UserLogin, UserRegister


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, data: UserRegister) -> User:
        result = await self.db.execute(select(User).where(User.email == data.email))
        email = result.scalars().first()
        if email is not None:
            raise AlreadyExistsError("Email already registered")
        else:
            user = User(email=data.email, hashed_password=hash_password(data.password))
            self.db.add(user)
            try:
                await self.db.commit()
            except IntegrityError:
                await self.db.rollback()
                raise AlreadyExistsError("Email already registered")
            await self.db.refresh(user)
            return user

    async def login(self, data: UserLogin) -> str:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalars().first()
        if user is None:
            raise InvalidCredentialsError()
        if not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError()
        return create_access_token(user.id)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    return AuthService(db)
