from fastapi import APIRouter, Depends, status

from src.models import User
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.schemas import Token, UserLogin, UserRead, UserRegister
from src.modules.auth.service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister, service: AuthService = Depends(get_auth_service)
):
    return await service.register(data)


@router.post("/login", response_model=Token)
async def login(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    token = await service.login(data)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user
