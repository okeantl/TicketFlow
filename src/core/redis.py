from redis.asyncio import Redis

from src.core.config import get_settings

config = get_settings()


redis = Redis.from_url(config.REDIS_URL, decode_responses=True)


async def get_redis():
    return redis
