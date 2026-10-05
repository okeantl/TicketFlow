from decimal import Decimal

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.broker import publish_message
from src.core.database import get_db
from src.core.exceptions import AlreadyExistsError, NotFoundError
from src.core.redis import get_redis
from src.models import Order, OrderItem, OrderStatus, Seat
from src.modules.orders.schemas import OrderCreate


class OrderService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def create_order(self, user_id: int, data: OrderCreate) -> Order:
        list_seat = []
        for seat_id in data.seat_ids:
            result = await self.db.execute(select(Seat).where(Seat.id == seat_id))
            seat = result.scalars().first()
            if seat is None:
                raise NotFoundError(detail=f"Seat is {seat_id} not found")
            locked = await self.redis.get(f"seat_lock:{seat_id}")
            if locked != str(user_id):
                raise AlreadyExistsError("Seat does not belong to this user")
            list_seat.append(seat)
        total_amount = Decimal(0)
        for seat in list_seat:
            total_amount += seat.price
        order = Order(
            user_id=user_id, status=OrderStatus.PENDING, total_amount=total_amount
        )
        self.db.add(order)
        await self.db.flush()
        for seat in list_seat:
            order_item = OrderItem(order_id=order.id, seat_id=seat.id, price=seat.price)
            self.db.add(order_item)
        await self.db.commit()
        await self.db.refresh(order)
        await publish_message(
            queue_name="payment.process", message={"order_id": order.id}
        )
        return order


def get_orders_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OrderService:
    return OrderService(db, redis)
