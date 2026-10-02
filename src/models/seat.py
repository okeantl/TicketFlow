import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.event import Event


class SeatStatus(enum.Enum):
    AVAILABLE = "available"
    HELD = "held"
    SOLD = "sold"


class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    row: Mapped[str] = mapped_column()
    number: Mapped[int] = mapped_column()
    status: Mapped[SeatStatus] = mapped_column(default=SeatStatus.AVAILABLE)

    event: Mapped["Event"] = relationship(back_populates="seats")
