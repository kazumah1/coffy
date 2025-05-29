from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class Contact(BaseModel):
    id: UUID
    user_id: UUID  # Owner of this contact
    name: str  # User-defined name (can be nicknames)
    phone_number: str  # For SMS outreach
    is_registered_user: bool  # Whether this contact has registered on the platform
    relationship_score: float  # For weighting responses (e.g. “best friends”)
    last_interaction: datetime  # For prioritizing recent contacts
    created_at: datetime
    updated_at: datetime