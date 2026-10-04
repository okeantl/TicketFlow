import asyncio

import aio_pika

from src.core.config import get_settings


async def main() -> None:
    connection = await aio_pika.connect_robust(get_settings().RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("payment.process", durable=True)
    await channel.declare_queue("payment.process.dlq", durable=True)

    async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            print("Received message", message.body.decode())

    await queue.consume(on_message)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
