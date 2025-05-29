from pydantic import BaseModel
from typing import List, UUID, Optional
from datetime import datetime

class Message(BaseModel):
    id: UUID
    conversation_id: UUID  # Refers to Conversation
    direction: str  # "inbound" (user → app) or "outbound" (app → user)
    content: str  # Raw SMS content
    parsed_data: Optional[dict]  # LLM-extracted info (e.g. times, sentiment)
    timestamp: datetime

class Conversation(BaseModel):
    id: UUID
    event_participant_id: UUID  # One-on-one SMS thread for a given event
    event_id: UUID
    messages: List[Message]  # Ordered list of Message objects
    status: str  # "active", "completed", "failed" (for retry logic or edge cases)
    created_at: datetime
    updated_at: datetime