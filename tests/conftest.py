import asyncio
import sys

import pytest
import pytest_asyncio
from alembic.config import Config
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic import command

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15", driver="psycopg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def apply_migrations(postgres_container):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_container.get_connection_url())
    command.upgrade(config, "head")
    yield


@pytest_asyncio.fixture
async def db_session(postgres_container, apply_migrations):
    engine = create_async_engine(
        postgres_container.get_connection_url(driver="psycopg")
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest_asyncio.fixture
async def redis_client(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(redis_container.port)

    client = Redis(host=host, port=port, decode_responses=True)
    yield client
    await client.aclose()
