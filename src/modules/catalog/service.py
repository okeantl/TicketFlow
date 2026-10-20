from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError
from src.core.redis import get_redis
from src.models import Event, Seat, SeatStatus
from src.modules.catalog.schemas import EventRead, SeatRead


class CatalogService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def list_events(self) -> list[Event]:
        events = select(Event)
        result = await self.db.execute(events)
        events_list = result.scalars().all()

        return list(events_list)

    async def get_event(self, event_id: int) -> Event | EventRead:
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
        raise NotFoundError("Event not found")

    async def list_seats(self, event_id: int) -> list[SeatRead]:
        await self.get_event(event_id)
        result = await self.db.execute(
            select(Seat)
            .where(Seat.event_id == event_id)
            .order_by(Seat.row, Seat.number)
        )
        seats = result.scalars().all()
        if not seats:
            return []
        locks = await self.redis.mget([f"seat_lock:{seat.id}" for seat in seats])
        seat_list = []
        for seat, lock in zip(seats, locks, strict=True):
            if seat.status == SeatStatus.SOLD:
                status = SeatStatus.SOLD
            elif lock is not None:
                status = SeatStatus.HELD
            else:
                status = SeatStatus.AVAILABLE
            seat_list.append(
                SeatRead(
                    id=seat.id,
                    row=seat.row,
                    number=seat.number,
                    price=seat.price,
                    status=status.value,
                )
            )
        return seat_list


def get_catalog_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CatalogService:
    return CatalogService(db, redis)
