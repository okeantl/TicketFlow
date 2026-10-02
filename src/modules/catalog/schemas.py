from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    starts_at: datetime
