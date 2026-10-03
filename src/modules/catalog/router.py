from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.catalog.schemas import EventRead
from src.modules.catalog.service import CatalogService, get_catalog_service

router = APIRouter(prefix="/events", tags=["catalog"])


@router.get("/", response_model=list[EventRead])
async def list_events(service: CatalogService = Depends(get_catalog_service)):
    return await service.list_events()


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: int, service: CatalogService = Depends(get_catalog_service)
):
    event = await service.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    else:
        return event
