from fastapi import APIRouter, Depends

from src.models import User
from src.modules.auth.dependencies import get_current_user
from src.modules.booking.schemas import SeatHoldResponse
from src.modules.booking.service import BookingService, get_booking_service

router = APIRouter(prefix="/seats", tags=["booking"])


@router.post("/{seat_id}/hold", response_model=SeatHoldResponse)
async def hold_seat(
    seat_id: int,
    service: BookingService = Depends(get_booking_service),
    user: User = Depends(get_current_user),
):
    return await service.hold_seat(seat_id, user.id)
