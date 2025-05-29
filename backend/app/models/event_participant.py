from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class EventParticipant(BaseModel):
    id: UUID
    event_id: UUID
    user_id: Optional[UUID]  # If they're a registered user
    phone_number: str
    name: str
    status: str  # "invited", "responded", "confirmed", "declined"
    availability: List[datetime]  # Their available time slots
    created_at: datetime
    updated_at: datetime