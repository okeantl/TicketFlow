import asyncio

import aio_pika

from src.core.config import get_settings

config = get_settings()
_connection: aio_pika.abc.AbstractRobustConnection | None = None


async def connect_broker() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    for attempt in range(1, 6):
        try:
            _connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
            return _connection
        except Exception as e:
            print(f"Попытка {attempt} не удалась: {e}")
            await asyncio.sleep(2)
    raise RuntimeError("Не удалось подключиться к RabbitMQ после 5 попыток")


async def close_broker() -> None:
    if _connection:
        await _connection.close()


def get_broker_connection():
    return _connection
