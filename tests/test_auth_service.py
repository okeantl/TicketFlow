import pytest

from src.core.exceptions import AlreadyExistsError
from src.modules.auth.schemas import UserRegister
from src.modules.auth.service import AuthService


async def test_register_creates_user(db_session):
    service = AuthService(db_session)
    data = UserRegister(email="pyrest@example.com", password="secret123")

    user = await service.register(data)

    assert user.id is not None
    assert user.email == "pyrest@example.com"
    assert user.hashed_password != "secret123"


async def test_register_duplicate_email_raises(db_session):
    service = AuthService(db_session)
    data = UserRegister(email="duplicate@example.com", password="secret123")

    await service.register(data)

    with pytest.raises(AlreadyExistsError):
        await service.register(data)
