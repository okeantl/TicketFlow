from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.redis import get_redis
from src.models import Event
from src.modules.catalog.schemas import EventRead


class CatalogService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def list_events(self) -> list[Event]:
        events = select(Event)
        result = await self.db.execute(events)
        events_list = result.scalars().all()

        return list(events_list)

    async def get_event(self, event_id: int) -> Event | EventRead | None:
        cache_key = f"event:{event_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return EventRead.model_validate_json(cached)
        events_id = select(Event).where(Event.id == event_id)
        result = await self.db.execute(events_id)
        event = result.scalars().first()
        if event is not None:
            await self.redis.set(
                cache_key, EventRead.model_validate(event).model_dump_json(), ex=60
            )
            return event
        return None


def get_catalog_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CatalogService:
    return CatalogService(db, redis)
