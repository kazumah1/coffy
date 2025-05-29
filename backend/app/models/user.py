from pydantic import BaseModel
from typing import Optional, UUID
from datetime import datetime

class User(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    phone_number: str
    google_calendar_token: Optional[str]
    contacts: list[str]
    preferences: dict
    created_at: datetime
    updated_at: datetime