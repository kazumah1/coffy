from pydantic import BaseModel
from typing import Optional, UUID
from datetime import datetime

class User(BaseModel):
    id: UUID  # Unique user ID
    name: str  # Full name
    email: Optional[str]  # Used for Google login/calendar
    phone_number: str  # For SMS identification
    google_calendar_token: Optional[str]  # OAuth token for Calendar API access
    contacts: List[UUID]  # Foreign keys to Contact objects
    preferences: dict  # App-level settings (e.g. default event times)
    created_at: datetime
    updated_at: datetime