from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AlreadyExistsError, NotFoundError
from src.core.redis import get_redis
from src.models import Seat, SeatStatus
from src.modules.booking.schemas import SeatHoldResponse

HOLD_TTL_SECONDS = 300


class BookingService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def hold_seat(self, seat_id: int, user_id: int) -> SeatHoldResponse:
        result = await self.db.execute(select(Seat).where(Seat.id == seat_id))
        seat = result.scalars().first()
        if seat is None:
            raise NotFoundError("Seat not found")
        if seat.status != SeatStatus.AVAILABLE:
            raise AlreadyExistsError("Seat is not available")
        locked = await self.redis.set(
            f"seat_lock:{seat_id}", str(user_id), nx=True, ex=HOLD_TTL_SECONDS
        )
        if not locked:
            raise AlreadyExistsError("Seat is currently held by another user")
        seat.status = SeatStatus.HELD
        await self.db.commit()

        return SeatHoldResponse(
            seat_id=seat.id,
            status=seat.status.value,
            held_until_seconds=HOLD_TTL_SECONDS,
        )


def get_booking_service(
    db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
) -> BookingService:
    return BookingService(db, redis)
