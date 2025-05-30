"""Model for time slots (busy or available) from participants."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class TimeSlot(BaseModel):
    """A time slot indicating when a participant is busy or available."""
    id: str = Field(..., description="Unique identifier for the time slot")
    participant_id: Optional[str] = Field(None, description="UUID of the registered participant (if registered)")
    phone_number: Optional[str] = Field(None, description="Phone number of the unregistered participant (if unregistered)")
    start_time: datetime = Field(..., description="Start time of the slot")
    end_time: datetime = Field(..., description="End time of the slot")
    slot_type: Literal["busy", "available"] = Field(..., description="Whether this is a busy or available time slot")
    source: Literal["calendar", "text"] = Field(..., description="Source of the time slot (calendar or text message)")
    confidence: Optional[float] = Field(None, description="Confidence score for text-based slots (0-1)")
    raw_text: Optional[str] = Field(None, description="Original text that generated this slot (for text-based slots)")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate that either participant_id or phone_number is provided
        if not self.participant_id and not self.phone_number:
            raise ValueError("Either participant_id or phone_number must be provided")
        if self.participant_id and self.phone_number:
            raise ValueError("Cannot provide both participant_id and phone_number") 