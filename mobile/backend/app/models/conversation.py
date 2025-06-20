from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class Message(BaseModel):
    id: UUID
    conversation_id: UUID  # Refers to Conversation
    direction: str  # "inbound" (user → app) or "outbound" (app → user)
    content: str  # Raw SMS content
    parsed_data: Optional[dict]  # LLM-extracted info (e.g. times, sentiment)
    timestamp: datetime
    to_number: str

class Conversation(BaseModel):
    id: UUID
    event_id: UUID
    phone_number: str # phone number used for identification for unregistered users
    user_id: Optional[UUID] # id of the registered user
    user_name: str # name of the unregistered user
    type: str # "unregistered" or "registered"
    messages: List[Message]  # Ordered list of Message objects
    status: str  # "active", "completed", "failed" (for retry logic or edge cases)
    created_at: datetime
    updated_at: datetime

class ChatSession(BaseModel):
    id: UUID
    user_id: UUID # id of the registered user
    messages: List[Message]  # Ordered list of Message objects