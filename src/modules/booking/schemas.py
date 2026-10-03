from pydantic import BaseModel


class SeatHoldResponse(BaseModel):
    seat_id: int
    status: str
    held_until_seconds: int
