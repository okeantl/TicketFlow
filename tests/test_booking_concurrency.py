import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from src.core.exceptions import AlreadyExistsError
from src.models.event import Event
from src.models.seat import Seat, SeatStatus
from src.modules.booking.schemas import SeatHoldResponse
from src.modules.booking.service import BookingService


async def test_concurrent_hold_only_one_succeeds(
    db_session, redis_client, session_factory
):
    event = Event(
        title="Test Concert",
        starts_at=datetime(2026, 12, 1, 19, 0, tzinfo=timezone.utc),
    )
    db_session.add(event)
    await db_session.flush()
    seat = Seat(
        event_id=event.id,
        row="A",
        number=1,
        price=Decimal("50.00"),
        status=SeatStatus.AVAILABLE,
    )
    db_session.add(seat)
    await db_session.commit()
    await db_session.refresh(seat)

    seat_id = seat.id

    async def hold(user_id: int):
        async with session_factory() as session:
            service = BookingService(session, redis_client)
            return await service.hold_seat(seat_id, user_id)

    results = await asyncio.gather(
        *(hold(user_id) for user_id in range(1, 11)), return_exceptions=True
    )

    successes = [r for r in results if isinstance(r, SeatHoldResponse)]
    failures = [r for r in results if isinstance(r, AlreadyExistsError)]
    assert len(successes) == 1
    assert len(failures) == 9

    winner_user_id = results.index(successes[0]) + 1
    assert await redis_client.get(f"seat_lock:{seat_id}") == str(winner_user_id)

    async with session_factory() as session:
        result = await session.execute(select(Seat).where(Seat.id == seat_id))
        assert result.scalars().one().status == SeatStatus.AVAILABLE
