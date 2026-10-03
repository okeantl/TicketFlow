from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.core.broker import close_broker, connect_broker, get_broker_connection
from src.core.config import get_settings
from src.core.database import engine
from src.core.exceptions import AppError
from src.core.logging import configure_logging
from src.core.redis import redis
from src.modules.auth.router import router as auth_router
from src.modules.booking.router import router as booking_router
from src.modules.catalog.router import router as catalog_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_broker()
    yield
    await close_broker()


settings = get_settings()
configure_logging(settings.LOG_LEVEL)
app = FastAPI(title="TicketFlow", lifespan=lifespan)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(catalog_router)
app.include_router(auth_router)
app.include_router(booking_router)


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
