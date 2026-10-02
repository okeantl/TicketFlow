from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Event
from src.modules.catalog.schemas import EventRead

router = APIRouter(prefix="/events", tags=["catalog"])


@router.get("/", response_model=list[EventRead])
async def list_events(db: AsyncSession = Depends(get_db)):
    events = select(Event)
    result = await db.execute(events)
    events_list = result.scalars().all()

    return events_list


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    events_id = select(Event).where(Event.id == event_id)
    result = await db.execute(events_id)
    events_get = result.scalars().first()
    if events_get is None:
        raise HTTPException(status_code=404, detail="Event not found")
    else:
        return events_get
