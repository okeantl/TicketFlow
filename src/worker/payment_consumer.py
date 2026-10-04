import asyncio
import json
import random
from typing import cast

import aio_pika
import structlog
from sqlalchemy import select

from src.core.broker import connect_broker, get_broker_channel, publish_message
from src.core.database import SessionLocal
from src.core.redis import redis
from src.models import Order
from src.models.order import OrderStatus
from src.models.order_item import OrderItem
from src.models.seat import Seat, SeatStatus

logger = structlog.get_logger(__name__)


def mock_charge_payment(amount) -> bool:
    num = random.random()
    if num >= 0.7:
        return False
    else:
        return True


async def main() -> None:
    await connect_broker()
    channel = get_broker_channel()
    if channel is None:
        raise RuntimeError("Broker channel is not initialized")
    queue = await channel.declare_queue("payment.process", durable=True)
    await channel.declare_queue("payment.process.dlq", durable=True)

    async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        MAX_RETRIES = 3
        retry_count = cast(int, (message.headers or {}).get("x-retry-count", 0))
        data = json.loads(message.body.decode())
        try:
            order_id = data["order_id"]
            async with SessionLocal() as db:
                result = await db.execute(select(Order).where(Order.id == order_id))
                order = result.scalars().first()
                if order is None:
                    return
                print(order)
                should_notify = False
                if mock_charge_payment(order.total_amount):
                    order.status = OrderStatus.PAID
                    result = await db.execute(
                        select(OrderItem).where(OrderItem.order_id == order.id)
                    )
                    order_item = result.scalars().all()
                    for item in order_item:
                        result = await db.execute(
                            select(Seat).where(Seat.id == item.seat_id)
                        )
                        seat = result.scalars().first()
                        if seat is None:
                            continue
                        seat.status = SeatStatus.SOLD
                        await redis.delete(f"seat_lock:{seat.id}")
                    should_notify = True
                else:
                    order.status = OrderStatus.FAILED
                await db.commit()
                if should_notify:
                    await publish_message(
                        "notification.send_ticket", {"order_id": order.id}
                    )
        except Exception as e:
            logger.warning(
                "payment_processing_failed",
                order_id=order_id,
                retry_count=retry_count,
                error=str(e),
            )
            if retry_count < MAX_RETRIES:
                await publish_message(
                    "payment.process",
                    {"order_id": order_id},
                    headers={"x-retry-count": retry_count + 1},
                )
            else:
                await publish_message("payment.process.dlq", {"order_id": order_id})

        await message.ack()

    await queue.consume(on_message)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
