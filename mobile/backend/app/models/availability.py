from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AvailabilitySlot(BaseModel):
    id: UUID
    participant_id: UUID  # Refers to EventParticipant
    start_time: datetime
    end_time: datetime
    source: str  # "calendar", "manual", or "parsed" (used to infer confidence)