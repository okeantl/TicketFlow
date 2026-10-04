import asyncio
import json

import structlog
from sqlalchemy import select

from src.core.broker import connect_broker, get_broker_channel
from src.core.database import SessionLocal
from src.models.order import Order
from src.models.order_item import OrderItem
from src.models.seat import Seat
from src.models.user import User

logger = structlog.get_logger(__name__)


async def main() -> None:
    await connect_broker()
    channel = get_broker_channel()
    if channel is None:
        raise RuntimeError("Broker channel is not initialized")
    queue = await channel.declare_queue("notification.send_ticket", durable=True)

    async def on_message(message):
        data = json.loads(message.body.decode())
        order_id = data["order_id"]
        try:
            async with SessionLocal() as db:
                result = await db.execute(select(Order).where(Order.id == order_id))
                order = result.scalars().first()
                if order is None:
                    return
                result = await db.execute(select(User).where(User.id == order.user_id))
                user = result.scalars().first()
                if user is None:
                    return
                result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id)
                )
                order_item = result.scalars().all()
                seats_info = []
                for item in order_item:
                    result = await db.execute(
                        select(Seat).where(Seat.id == item.seat_id)
                    )
                    seat = result.scalars().first()
                    if seat is None:
                        continue
                    seats_info.append(f"{seat.row}{seat.number}")
                logger.info(
                    f"отправлен билет на {user.email} для заказа{order_id} места {seats_info}"
                )
        except Exception as e:
            logger.warning(
                "notification_failed",
                order_id=order_id,
                error=str(e),
            )
        await message.ack()

    await queue.consume(on_message)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
