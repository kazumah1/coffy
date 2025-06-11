from pydantic import BaseModel
from typing import Optional, UUID, List
from datetime import datetime

class User(BaseModel):
    id: UUID  # Unique user ID
    name: str  # Full name
    email: Optional[str]  # Used for Google login/calendar
    phone_number: str  # For SMS identification
    google_access_token: Optional[str]  # OAuth token for Calendar API access
    google_refresh_token: Optional[str]  # Refresh token for Calendar API access
    google_token_expiry: Optional[datetime]  # Expiry time for Google token
    contacts: List[UUID]  # Foreign keys to Contact objects
    preferences: dict  # App-level settings (e.g. default event times)
    created_at: datetime
    updated_at: datetime