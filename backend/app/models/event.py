from pydantic import BaseModel
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

class Event(BaseModel):
    id: UUID
    creator_id: UUID  # Refers to User.id
    event_type: str  # e.g. “dinner”, “coffee”
    title: str  # Optional label (e.g. “Dinner with friends”)
    description: Optional[str]
    status: str  # "pending", "confirmed", "cancelled"
    proposed_times: List[Tuple[datetime, datetime]]  # Candidate slots (start, end)
    final_time: Optional[Tuple[datetime, datetime]]  # Chosen confirmed time
    location: Optional[str]  # Venue or meeting point
    recurrence: Optional[str]  # e.g. "weekly", "monthly"
    created_at: datetime
    updated_at: datetime