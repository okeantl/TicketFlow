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

RELEASE_LOCK_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""


def mock_charge_payment(amount) -> bool:
    num = random.random()
    return num < 0.7


def parse_order_id(body: bytes) -> int | None:
    try:
        data = json.loads(body.decode())
        value = data["order_id"]
    except (ValueError, KeyError, TypeError):
        return None

    if not isinstance(value, int):
        return None
    return value


async def main() -> None:
    await connect_broker()
    channel = get_broker_channel()
    if channel is None:
        raise RuntimeError("Broker channel is not initialized")
    queue = await channel.declare_queue("payment.process", durable=True)
    await channel.declare_queue("payment.process.dlq", durable=True)

    async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        order_id: int | None = None
        MAX_RETRIES = 3
        retry_count = cast(int, (message.headers or {}).get("x-retry-count", 0))
        try:
            order_id = parse_order_id(message.body)
            if order_id is None:
                raw = message.body.decode(errors="replace")
                logger.warning("malformed_message", raw=raw)
                await publish_message("payment.process.dlq", {"raw": raw})
                return
            async with SessionLocal() as db:
                result = await db.execute(
                    select(Order).where(Order.id == order_id).with_for_update()
                )
                order = result.scalars().first()
                if order is None:
                    logger.warning(
                        "order_not_found",
                        order_id=order_id,
                    )
                    return
                if order.status is not OrderStatus.PENDING:
                    logger.info(
                        "order_already_processed",
                        order_id=order_id,
                        status=order.status.value,
                    )
                    return
                should_notify = False
                order_item_result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id)
                )
                order_item = order_item_result.scalars().all()
                seat_ids = [item.seat_id for item in order_item]
                sold_result = await db.execute(
                    select(Seat.id).where(
                        Seat.id.in_(seat_ids),
                        Seat.status == SeatStatus.SOLD,
                    )
                )
                already_sold = sold_result.scalars().first() is not None
                if already_sold:
                    logger.warning("seat_already_sold", order_id=order_id)
                    order.status = OrderStatus.FAILED
                elif mock_charge_payment(order.total_amount):
                    order.status = OrderStatus.PAID
                    for item in order_item:
                        seat_result = await db.execute(
                            select(Seat).where(Seat.id == item.seat_id)
                        )
                        seat = seat_result.scalars().first()
                        if seat is None:
                            continue
                        seat.status = SeatStatus.SOLD
                    should_notify = True
                else:
                    order.status = OrderStatus.FAILED
                await db.commit()
                keys = [f"seat_lock:{item.seat_id}" for item in order_item]
                for key in keys:
                    await redis.eval(RELEASE_LOCK_SCRIPT, 1, key, str(order.user_id))
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
        finally:
            await message.ack()

    await queue.consume(on_message)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
