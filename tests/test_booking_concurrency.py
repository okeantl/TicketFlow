import asyncio
from datetime import datetime
from decimal import Decimal

from src.core.exceptions import AlreadyExistsError
from src.models.event import Event
from src.models.seat import Seat, SeatStatus
from src.modules.booking.service import BookingService


async def test_concurrent_hold_only_one_succeeds(db_session, redis_client):
    event = Event(title="Test Concert", starts_at=datetime(2026, 12, 1, 19, 0))
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

    service = BookingService(db_session, redis_client)
    tasks = [service.hold_seat(seat.id, user_id) for user_id in range(1, 11)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, AlreadyExistsError)]

    assert len(successes) == 1
    assert len(failures) == 9
