import aio_pika

from src.core.config import get_settings

config = get_settings()
_connection: aio_pika.abc.AbstractRobustConnection | None = None


async def connect_broker():
    global _connection
    _connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
    return _connection


async def close_broker() -> None:
    if _connection:
        await _connection.close()


def get_broker_connection():
    return _connection
