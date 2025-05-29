from pydantic import BaseModel
from typing import List, UUID, datetime


class Conversation:
    id: UUID
    event_id: UUID
    participant_id: UUID
    messages: List[Message]
    status: str  # "active", "completed", "failed"
    created_at: datetime
    updated_at: datetime

class Message:
    id: UUID
    conversation_id: UUID
    direction: str  # "inbound" or "outbound"
    content: str
    timestamp: datetime