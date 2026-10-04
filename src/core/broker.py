import asyncio
import json

import aio_pika
import structlog
from aio_pika.abc import HeadersType

from src.core.config import get_settings

logger = structlog.get_logger(__name__)

config = get_settings()
_connection: aio_pika.abc.AbstractRobustConnection | None = None
_channel: aio_pika.abc.AbstractRobustChannel | None = None


async def connect_broker() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    global _channel
    for attempt in range(1, 6):
        try:
            _connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
            _channel = await _connection.channel()
            return _connection
        except Exception as e:
            logger.warning("rabbitmq_connect_retry", attempt=attempt, error=str(e))
            await asyncio.sleep(2)
    raise RuntimeError("Не удалось подключиться к RabbitMQ после 5 попыток")


async def publish_message(
    queue_name: str, message: dict, headers: dict | None = None
) -> None:
    if _channel is None:
        raise RuntimeError(
            "Broker channel is not initialized - call connect_broker() first"
        )
    await _channel.declare_queue(queue_name, durable=True)
    await _channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode(), headers=headers or {}),
        routing_key=queue_name,
    )


async def close_broker() -> None:
    if _connection:
        await _connection.close()


def get_broker_connection():
    return _connection


def get_broker_channel():
    return _channel
