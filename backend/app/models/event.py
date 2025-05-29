from pydantic import BaseModel
from typing import List, Optional, UUID
from datetime import datetime

class Event(BaseModel):
    id: UUID
    creator_id: UUID
    event_type: str  # e.g., "dinner", "coffee"
    title: str
    description: Optional[str]
    status: str  # "pending", "confirmed", "cancelled"
    proposed_times: List[datetime]
    final_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    invitees: list[str]
    responses: dict[str, str]