from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class EventParticipant(BaseModel):
    id: UUID
    event_id: UUID  # Refers to Event
    user_id: Optional[UUID]  # If the person is a registered user
    phone_number: str  # Always included (used for SMS)
    name: str  # Display name
    status: str  # "invited", "responded", "confirmed", "declined"
    response_text: Optional[str]  # Raw reply string (for LLM use/fallback)
    availability_slots: List[Tuple[datetime, datetime]]  # Interpreted free time ranges
    created_at: datetime
    updated_at: datetime