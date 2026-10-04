from fastapi import APIRouter, Depends, status

from src.models import User
from src.modules.auth.dependencies import get_current_user
from src.modules.orders.schemas import OrderCreate, OrderRead
from src.modules.orders.service import OrderService, get_orders_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_orders(
    data: OrderCreate,
    service: OrderService = Depends(get_orders_service),
    user: User = Depends(get_current_user),
):
    return await service.create_order(user.id, data)
