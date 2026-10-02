from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.core.broker import close_broker, connect_broker, get_broker_connection
from src.core.database import engine
from src.core.redis import redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_broker()
    yield
    await close_broker()


app = FastAPI(title="TicketFlow", lifespan=lifespan)


@app.get("/health")
async def get_health():
    status = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {e}"

    try:
        await redis.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {e}"

    try:
        conn = get_broker_connection()
        if conn is not None and not conn.is_closed:
            status["rabbitmq"] = "ok"
        else:
            status["rabbitmq"] = "error: not connected"
    except Exception as e:
        status["rabbitmq"] = f"error: {e}"

    healthy = all(v == "ok" for v in status.values())
    return JSONResponse(content=status, status_code=200 if healthy else 503)
