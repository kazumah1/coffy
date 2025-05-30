from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class Contact(BaseModel):
    owner_id: UUID # user id of the contact list owner
    recipient_id: Optional[UUID]  # user id of the contact, only set once user registers
    name: str  # User-defined name
    phone_number: str  # For SMS outreach
    is_registered: bool  # Whether this contact has registered on the platform
    relationship_score: float  # For weighting responses (e.g. "best friends") 0-100
    last_interaction: datetime  # For prioritizing recent contacts
    created_at: datetime
    updated_at: datetime