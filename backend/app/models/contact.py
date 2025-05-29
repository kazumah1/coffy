from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class Contact:
    id: UUID
    user_id: UUID  # Owner of this contact
    name: str
    phone_number: str
    relationship_score: float  # For "best friend" prioritization
    last_interaction: datetime
    created_at: datetime
    updated_at: datetime