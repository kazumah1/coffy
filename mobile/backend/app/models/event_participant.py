from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime

class EventParticipant(BaseModel):
    id: Optional[UUID] # same as user_id if registered, otherwise empty
    event_id: UUID  # Refers to Event
    phone_number: str  # Always included (used for SMS)
    name: str  # Contact name
    registered: bool  # Whether the person is a registered user (use contact or user table to check)
    status: str  # 
    response_text: Optional[str]  # Raw reply string (for LLM use/fallback)
    availability_slots: List[Tuple[datetime, datetime]]  # Interpreted free time ranges
    created_at: datetime
    updated_at: datetime

    def update(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)