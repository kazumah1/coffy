import os
import requests
import json
from typing import Optional, Dict, List, Any
from .tools import AVAILABLE_TOOLS
from services.database_service import DatabaseService
from core.config import settings
from services.google_calendar_service import GoogleCalendarService
from services.token_manager import TokenManager
from services.texting_service import TextingService
from uuid import uuid4, UUID
from models.time_slot import TimeSlot
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging
from pydantic import BaseModel, Field, validator

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-3.5-turbo:free"

SYSTEM_PROMPT = (
    """
You are a calendar assistant. Take the user's request and return ONLY valid JSON matching this schema:

{
  "event": {
    "title":        "string",
    "start_time":   "string in ISO 8601 format",
    "end_time":     "string in ISO 8601 format",
    "location":     "string or null"
  },
  "participants": [
    {
      "name":         "string",
      "email":        "string or null",
      "role":         "string"
    }
  ]
}

Respond with ONLY the JSON object, no additional text. Do NOT include any explanatory text.
"""
)

logger = logging.getLogger(__name__)

class OpenRouterError(Exception):
    """Base exception for OpenRouter service errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class EventResponse(BaseModel):
    """Model for validating event responses"""
    event_id: UUID
    phone_number: str = Field(..., pattern=r'^\+?1?\d{10,15}$')
    response: str = Field(..., min_length=1, max_length=1000)

    @validator('response')
    def validate_response(cls, v):
        valid_responses = ['yes', 'no', 'maybe']
        if v.lower() not in valid_responses:
            raise ValueError(f"Response must be one of: {', '.join(valid_responses)}")
        return v.lower()

class AvailabilityRequest(BaseModel):
    """Model for validating availability requests"""
    event_id: UUID
    phone_number: str = Field(..., pattern=r'^\+?1?\d{10,15}$')
    message: str = Field(..., min_length=1, max_length=1000)

class TimeSlotRequest(BaseModel):
    """Model for validating time slot requests"""
    event_id: UUID
    phone_number: str = Field(..., pattern=r'^\+?1?\d{10,15}$')
    start_time: datetime
    end_time: datetime

    @validator('end_time')
    def validate_time_range(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("End time must be after start time")
        return v

class OpenRouterService:
    def __init__(
        self,
        db_service: DatabaseService,
        google_calendar_service: GoogleCalendarService,
        token_manager: TokenManager,
        texting_service: TextingService
    ):
        self.api_url = API_URL
        self.model = MODEL
        self.api_key = settings.openrouter_api_key
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set in environment")
        self._current_event_id: Optional[str] = None
        self._current_owner_id: Optional[str] = None  # ID of the registered user making the request
        self.db_service = db_service
        self.google_calendar_service = google_calendar_service
        self.token_manager = token_manager
        self.texting_service = texting_service
        self.available_tools = AVAILABLE_TOOLS

    @property
    def current_event_id(self) -> Optional[str]:
        # Get the ID of the event currently being worked on
        return self._current_event_id

    def set_current_event(self, event_id: str) -> None:
        # Set the ID of the event currently being worked on
        self._current_event_id = event_id

    def clear_current_event(self) -> None:
        # Clear the current event ID
        self._current_event_id = None
        self._current_owner_id = None

    def _handle_error(self, error: Exception, context: str) -> None:
        """Standardized error handling for the service"""
        if isinstance(error, OpenRouterError):
            logger.error(f"{context}: {error.message}")
            raise HTTPException(status_code=error.status_code, detail=error.message)
        else:
            logger.error(f"{context}: Unexpected error: {str(error)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    async def prompt_agent(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send a prompt to the OpenRouter agent and get a response"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": settings.backend_url,
                "X-Title": "W2M Calendar Assistant"
            }
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            json_response = response.json()
            raw = json_response.get("choices", [{}])[0].get("message", {}).get("content")
            if not isinstance(raw, str):
                raise RuntimeError("unexpected response from OpenRouter")
            try:
                parsed = json.loads(raw)
            except Exception:
                raise RuntimeError(f"invalid JSON from llm:\n{raw}")
            return parsed
        except Exception as e:
            self._handle_error(e, "Failed to prompt agent")

    async def create_draft_event(self, creator_id: UUID, title: str, description: Optional[str] = None) -> dict:
        """Create a draft event"""
        try:
            event = await self.db_service.create_draft_event(creator_id, title, description)
            self.set_current_event(event["id"])
            self._current_owner_id = creator_id  # Store the registered user's ID
            return event
        except Exception as e:
            self._handle_error(e, "Failed to create draft event")

    async def create_event_participant(
        self,
        phone_number: str,
        name: str
    ) -> dict:
        # Create a participant for the current event
        if not self.current_event_id:
            raise RuntimeError("No current event set")
            
        return await self.db_service.create_event_participant(
            self.current_event_id,
            phone_number,
            name
        )

    async def search_contacts(
        self,
        query: str = None,
        min_relationship_score: float = None,
        recent_only: bool = False,
        limit: int = 15,
        days_ago: int = 30
    ) -> list[dict]:
        # Search contacts with flexible filtering
        if not self._current_owner_id:
            raise RuntimeError("No current owner set - create an event first")
            
        return await self.db_service.search_contacts(
            self._current_owner_id,  # Use the registered user's ID to find their contacts
            query,
            min_relationship_score,
            recent_only,
            limit,
            days_ago
        )

    async def get_google_calendar_busy_times(
        self,
        user_id: str,
        start_date: str,
        end_date: str
    ) -> list[dict]:
        """Get busy times from a registered user's Google Calendar within a date range."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Verify user is registered and has Google Calendar access
        tokens = await self.token_manager.get_token(user_id)
        if not tokens:
            raise RuntimeError(f"User {user_id} not found or not registered with Google Calendar")
            
        # Get events from Google Calendar
        events = self.google_calendar_service.get_all_events(
            tokens['google_access_token'],
            start_date,
            end_date
        )
        
        # Convert events to busy time slots
        busy_slots = []
        for event in events:
            # Skip events that are marked as free
            if event.get('transparency') == 'transparent':
                continue
                
            busy_slots.append({
                "id": str(uuid4()),
                "participant_id": user_id,
                "start_time": event['start'].get('dateTime', event['start'].get('date')),
                "end_time": event['end'].get('dateTime', event['end'].get('date')),
                "source": "calendar"
            })
            
        # Store the busy times in the database
        await self.db_service.store_participant_busy_times(
            self.current_event_id,
            user_id,
            busy_slots
        )
            
        return busy_slots

    async def create_availability_conversation(
        self,
        phone_number: str,
        user_name: str,
        user_id: str = None
    ) -> dict:
        """Creates an availability conversation - a shorter one for registered users (with user_id) or a detailed SMS-based one for unregistered users."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching one
        participants = await self.db_service.get_event_participants(self.current_event_id)
        participant = next(
            (p for p in participants 
             if p["phone_number"] == phone_number),
            None
        )
        
        if not participant:
            raise RuntimeError(
                f"No participant found with phone number {phone_number} - "
                "create participant first using create_event_participant"
            )
            
        # Verify participant registration status matches user_id
        if user_id and not participant["registered"]:
            raise RuntimeError(
                f"Participant {phone_number} is not registered but user_id was provided"
            )
        if not user_id and participant["registered"]:
            raise RuntimeError(
                f"Participant {phone_number} is registered but no user_id was provided"
            )
        
        # Create conversation for this availability request
        conversation = await self.db_service.create_conversation(
            self.current_event_id,
            phone_number,
            user_name,
            "availability_request",
            user_id
        )
        
        # Get event details for the message
        event = await self.db_service.get_event_by_id(self.current_event_id)
        if not event:
            raise RuntimeError(f"Event {self.current_event_id} not found")
            
        # Format message based on user type
        if user_id:
            # For registered users, ask for confirmation and preferences
            message = (
                f"Hi {user_name}! We're trying to schedule '{event['title']}'. "
                "Would you like me to check your calendar for availability? "
                "Please reply with 'yes' to let me check your calendar, or let me know your preferences."
            )
        else:
            # For unregistered users, ask for availability directly
            message = (
                f"Hi {user_name}! We're trying to schedule '{event['title']}'. "
                "Could you let me know when you're available? "
                "Please include any times you're busy or available."
            )
            
        try:
            # Send the initial message
            await self.texting_service.send_message(phone_number, message)
            
            # Update conversation status
            await self.db_service.update_conversation_status(
                self.current_event_id,
                phone_number,
                "message_sent"
            )
            
        except Exception as e:
            # Update conversation status to failed
            await self.db_service.update_conversation_status(
                self.current_event_id,
                phone_number,
                "failed"
            )
            raise RuntimeError(f"Failed to send availability request: {str(e)}")
        
        return conversation

    async def create_unregistered_time_slots(
        self,
        phone_number: str,
        time_slots: list[dict]
    ) -> list[dict]:
        """Store time slots for an unregistered user based on their text responses."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching unregistered one
        participants = await self.db_service.get_event_participants(self.current_event_id)
        participant = next(
            (p for p in participants 
             if p["phone_number"] == phone_number and not p["registered"]),
            None
        )
        if not participant:
            raise RuntimeError(f"No unregistered participant found with phone number {phone_number}")
            
        # Verify there's an active conversation for this participant
        conversations = await self.db_service.get_conversations(
            self.current_event_id,
            phone_number
        )
        if not any(c["type"] == "availability_request" and c["status"] == "active" 
                  for c in conversations):
            raise RuntimeError(
                f"No active availability conversation found for {phone_number} - "
                "create conversation first using create_availability_conversation"
            )
            
        # Convert raw slots to TimeSlot objects
        formatted_slots = []
        for slot in time_slots:
            time_slot = TimeSlot(
                id=str(uuid4()),
                phone_number=phone_number,
                start_time=datetime.fromisoformat(slot["start_time"]),
                end_time=datetime.fromisoformat(slot["end_time"]),
                slot_type=slot["slot_type"],
                source="text",
                confidence=slot.get("confidence"),
                raw_text=slot.get("raw_text")
            )
            formatted_slots.append(time_slot.dict())
            
        # Store the time slots
        await self.db_service.store_unregistered_time_slots(
            self.current_event_id,
            phone_number,
            formatted_slots
        )
        
        # Update conversation status if we got valid slots
        if formatted_slots:
            await self.db_service.update_conversation_status(
                self.current_event_id,
                phone_number,
                "completed"
            )
        
        return formatted_slots

    async def check_user_registration(self, phone_number: str) -> dict:
        """Check if a phone number belongs to a registered user and return their registration details and Google Calendar access status."""
        try:
            # Check if user exists in database
            user = await self.db_service.get_user_by_phone(phone_number)
            
            if not user:
                return {
                    "is_registered": False,
                    "user_id": None,
                    "name": None,
                    "has_google_calendar": False
                }
                
            # Check if user has Google Calendar access
            has_google_calendar = False
            try:
                tokens = await self.token_manager.get_token(user["id"])
                has_google_calendar = bool(tokens)
            except Exception:
                # If token retrieval fails, user doesn't have Google Calendar access
                pass
                
            return {
                "is_registered": True,
                "user_id": user["id"],
                "name": user["name"],
                "has_google_calendar": has_google_calendar
            }
            
        except Exception as e:
            raise RuntimeError(f"Error checking user registration: {str(e)}")

    async def send_availability_request(
        self,
        phone_number: str,
        start_date: str,
        end_date: str,
        event_title: str
    ) -> dict:
        """Send an initial availability request to an unregistered user via SMS."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching unregistered one
        participants = await self.db_service.get_event_participants(self.current_event_id)
        participant = next(
            (p for p in participants 
             if p["phone_number"] == phone_number and not p["registered"]),
            None
        )
        if not participant:
            raise RuntimeError(f"No unregistered participant found with phone number {phone_number}")
            
        # Get active availability conversation
        conversations = await self.db_service.get_conversations(
            self.current_event_id,
            phone_number
        )
        conversation = next(
            (c for c in conversations 
             if c["type"] == "availability_request" and c["status"] == "active"),
            None
        )
        if not conversation:
            raise RuntimeError(
                f"No active availability conversation found for {phone_number} - "
                "create conversation first using create_availability_conversation"
            )
            
        # Format the message
        message = (
            f"Hi {participant['name']}! We're trying to schedule '{event_title}'. "
            f"Could you let me know when you're available between {start_date} and {end_date}? "
            "Please include any times you're busy or available."
        )
        
        try:
            # Send the message
            await self.texting_service.send_message(phone_number, message)
            
            # Update conversation status
            await self.db_service.update_conversation_status(
                self.current_event_id,
                phone_number,
                "message_sent"
            )
            
            return {
                "success": True,
                "conversation_id": conversation["id"],
                "message": message
            }
            
        except Exception as e:
            # Update conversation status to failed
            await self.db_service.update_conversation_status(
                self.current_event_id,
                phone_number,
                "failed"
            )
            raise RuntimeError(f"Failed to send availability request: {str(e)}")

    async def parse_availability_response(
        self,
        phone_number: str,
        response_text: str,
        user_id: str = None
    ) -> dict:
        """Parse user's availability response - for registered users checks calendar permission and fetches data, 
        for unregistered users extracts and stores time slots from text."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching one
        participants = await self.db_service.get_event_participants(self.current_event_id)
        participant = next(
            (p for p in participants 
             if p["phone_number"] == phone_number),
            None
        )
        if not participant:
            raise RuntimeError(f"No participant found with phone number {phone_number}")
            
        # Get active availability conversation
        conversations = await self.db_service.get_conversations(
            self.current_event_id,
            phone_number
        )
        conversation = next(
            (c for c in conversations 
             if c["type"] == "availability_request" and c["status"] == "active"),
            None
        )
        if not conversation:
            raise RuntimeError(
                f"No active availability conversation found for {phone_number} - "
                "create conversation first using create_availability_conversation"
            )
            
        # For registered users, check if they've given calendar permission
        if user_id:
            # Check if response indicates permission to access calendar
            calendar_permission = any(word in response_text.lower() 
                                    for word in ["yes", "sure", "ok", "okay", "fine", "go ahead"])
            
            if calendar_permission:
                try:
                    # Get their busy times for the next 7 days
                    start_date = datetime.now().date().isoformat()
                    end_date = (datetime.now() + timedelta(days=7)).date().isoformat()
                    
                    busy_times = await self.get_google_calendar_busy_times(
                        user_id,
                        start_date,
                        end_date
                    )
                    
                    # Store the busy times
                    await self.db_service.store_participant_busy_times(
                        self.current_event_id,
                        user_id,
                        busy_times
                    )
                    
                    # Update conversation status
                    await self.db_service.update_conversation_status(
                        self.current_event_id,
                        phone_number,
                        "completed"
                    )
                    
                    return {
                        "success": True,
                        "calendar_accessed": True,
                        "time_slots": busy_times,
                        "message": "Thanks! I've checked your calendar and noted your availability."
                    }
                    
                except Exception as e:
                    # If calendar check fails, treat as manual availability
                    print(f"Failed to get calendar for registered user {user_id}: {str(e)}")
                    calendar_permission = False
            
            # If no calendar permission or calendar check failed, treat as manual availability
            if not calendar_permission:
                # Use LLM to extract time slots from response
                time_slots = await self._extract_time_slots_from_text(response_text)
                
                # Store the time slots
                await self.db_service.store_participant_busy_times(
                    self.current_event_id,
                    user_id,
                    time_slots
                )
                
                # Update conversation status
                await self.db_service.update_conversation_status(
                    self.current_event_id,
                    phone_number,
                    "completed"
                )
                
                return {
                    "success": True,
                    "calendar_accessed": False,
                    "time_slots": time_slots,
                    "message": "Thanks! I've noted your availability."
                }
                
        else:
            # For unregistered users, extract time slots from response
            time_slots = await self._extract_time_slots_from_text(response_text)
            
            # Store the time slots
            await self.db_service.store_unregistered_time_slots(
                self.current_event_id,
                phone_number,
                time_slots
            )
            
            # Update conversation status
            await self.db_service.update_conversation_status(
                self.current_event_id,
                phone_number,
                "completed"
            )
            
            return {
                "success": True,
                "calendar_accessed": False,
                "time_slots": time_slots,
                "message": "Thanks! I've noted your availability."
            }

    async def _extract_time_slots_from_text(self, text: str) -> list[dict]:
        """Extracts time slots from text using LLM.
        
        Returns list of dicts with start/end times (ISO format), slot_type (busy/available),
        confidence score (0-1), and raw text that generated each slot."""
        # Create a prompt for the LLM to extract time slots
        prompt = f"""
        Extract time slots from this text response about availability. Return ONLY valid JSON matching this schema:

        {{
          "time_slots": [
            {{
              "start_time": "string in ISO format (YYYY-MM-DDTHH:MM:SS)",
              "end_time": "string in ISO format (YYYY-MM-DDTHH:MM:SS)",
              "slot_type": "busy" or "available",
              "confidence": number between 0 and 1,
              "raw_text": "original text that generated this slot"
            }}
          ]
        }}

        Rules:
        1. If a time is mentioned without a date, assume today or tomorrow
        2. If only a date is mentioned, assume 9am-5pm for that day
        3. If a time range is mentioned (e.g. "2-4pm"), create a slot for that range
        4. If a specific time is mentioned (e.g. "3pm"), create a 1-hour slot
        5. If a day is mentioned (e.g. "Monday"), create a slot for that day
        6. Set confidence based on how clear the time reference is
        7. Include the original text that generated each slot

        Text to parse:
        {text}
        """
        
        try:
            # Call OpenRouter to extract time slots
            response = await self.prompt_agent(prompt)
            
            # Validate response format
            if not isinstance(response, dict) or "time_slots" not in response:
                raise RuntimeError("Invalid response format from LLM")
                
            time_slots = response["time_slots"]
            
            # Validate each time slot
            for slot in time_slots:
                # Check required fields
                if not all(k in slot for k in ["start_time", "end_time", "slot_type"]):
                    raise RuntimeError("Missing required fields in time slot")
                    
                # Validate slot type
                if slot["slot_type"] not in ["busy", "available"]:
                    raise RuntimeError(f"Invalid slot type: {slot['slot_type']}")
                    
                # Validate datetime format
                try:
                    datetime.fromisoformat(slot["start_time"])
                    datetime.fromisoformat(slot["end_time"])
                except ValueError:
                    raise RuntimeError(f"Invalid datetime format in slot: {slot}")
                    
                # Validate confidence if present
                if "confidence" in slot:
                    if not isinstance(slot["confidence"], (int, float)):
                        raise RuntimeError(f"Invalid confidence value: {slot['confidence']}")
                    if not 0 <= slot["confidence"] <= 1:
                        raise RuntimeError(f"Confidence must be between 0 and 1: {slot['confidence']}")
                        
            return time_slots
            
        except Exception as e:
            print(f"Error extracting time slots: {str(e)}")
            # Return empty list if extraction fails
            return []

    async def schedule_event(
        self,
        event_id: str,
        final_time: str,
        location: str = None,
        duration_minutes: int = 60
    ) -> dict:
        """Schedule event with final details and notify participants. Returns updated event info and notification status."""
        try:
            # Validate the event exists and get its details
            event = await self.db_service.get_event_by_id(event_id)
            if not event:
                raise RuntimeError(f"Event {event_id} not found")
                
            # Calculate end time based on duration
            start_time = datetime.fromisoformat(final_time)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Update event with final details
            update_data = {
                "status": "scheduled",
                "final_time": final_time,
                "end_time": end_time.isoformat(),
                "location": location
            }
            
            updated_event = await self.db_service.update_event(event_id, update_data)
            
            # Get all participants
            participants = await self.db_service.get_event_participants(event_id)
            
            # Send notifications to all participants
            notification_results = []
            for participant in participants:
                try:
                    # Format message based on participant type
                    if participant["registered"]:
                        message = (
                            f"Hi {participant['name']}! Your event '{event['title']}' has been scheduled "
                            f"for {start_time.strftime('%A, %B %d at %I:%M %p')}"
                        )
                        if location:
                            message += f" at {location}"
                        message += "."
                    else:
                        message = (
                            f"Hi {participant['name']}! Your event '{event['title']}' has been scheduled "
                            f"for {start_time.strftime('%A, %B %d at %I:%M %p')}"
                        )
                        if location:
                            message += f" at {location}"
                        message += ". Please let me know if you can make it!"
                    
                    # Send the message
                    await self.texting_service.send_message(
                        participant["phone_number"],
                        message
                    )
                    
                    # Create a new conversation for the event invitation
                    conversation = await self.db_service.create_conversation(
                        event_id,
                        participant["phone_number"],
                        participant["name"],
                        "event_invitation",
                        participant.get("id")  # user_id for registered users
                    )
                    
                    notification_results.append({
                        "participant_id": participant["id"],
                        "phone_number": participant["phone_number"],
                        "status": "sent",
                        "conversation_id": conversation["id"]
                    })
                    
                except Exception as e:
                    notification_results.append({
                        "participant_id": participant["id"],
                        "phone_number": participant["phone_number"],
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "event": updated_event,
                "notifications": notification_results
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to schedule event: {str(e)}")

    async def handle_event_response(
        self,
        event_id: UUID,
        phone_number: str,
        response_text: str
    ) -> dict:
        """Handle a participant's response to an event invitation"""
        try:
            # Validate input
            request = EventResponse(
                event_id=event_id,
                phone_number=phone_number,
                response=response_text
            )

            # Get event details
            event = await self.db_service.get_event_by_id(request.event_id)
            if not event:
                raise OpenRouterError(f"Event not found: {request.event_id}", 404)

            # Get participant details
            participant = await self.db_service.get_event_participant_by_phone(request.event_id, request.phone_number)
            if not participant:
                raise OpenRouterError(f"No participant found with phone number {request.phone_number}", 404)
                
            # Get active invitation conversation
            conversations = await self.db_service.get_conversations(request.event_id, request.phone_number)
            conversation = next(
                (c for c in conversations 
                 if c["type"] == "event_invitation" and c["status"] == "invitation_sent"),
                None
            )
            if not conversation:
                raise OpenRouterError(
                    f"No active invitation conversation found for {request.phone_number} - "
                    "send invitation first using send_event_invitation",
                    400
                )
                
            # Parse response using LLM
            prompt = f"""
            Parse this response to an event invitation. Return ONLY valid JSON matching this schema:

            {{
              "response_type": "accept" or "decline" or "maybe" or "custom",
              "confidence": number between 0 and 1,
              "custom_message": "string (only if response_type is custom)"
            }}

            Rules:
            1. "accept" for: yes, sure, ok, okay, fine, I'll be there, etc.
            2. "decline" for: no, sorry, can't make it, etc.
            3. "maybe" for: maybe, not sure, I'll try, etc.
            4. "custom" for: other responses that need human attention
            5. Set confidence based on how clear the response is
            6. Include the original message if response_type is custom

            Response to parse:
            {request.response}
            """
            
            try:
                # Call OpenRouter to parse response
                response = await self.prompt_agent(prompt)
                
                # Validate response format
                if not isinstance(response, dict):
                    raise RuntimeError("Invalid response format from LLM")
                    
                response_type = response.get("response_type")
                if response_type not in ["accept", "decline", "maybe", "custom"]:
                    raise RuntimeError(f"Invalid response type: {response_type}")
                    
                # Update participant status
                update_data = {
                    "status": response_type,
                    "response_text": request.response,
                    "updated_at": datetime.now()
                }
                
                # For registered users, update their calendar if they accepted
                if participant["registered"] and response_type == "accept":
                    try:
                        # Get their tokens
                        tokens = await self.token_manager.get_token(participant["id"])
                        
                        # Add event to their calendar
                        await self.google_calendar_service.add_event(
                            tokens["google_access_token"],
                            event["title"],
                            event["final_time"],
                            event["end_time"],
                            event.get("location"),
                            event.get("description")
                        )
                    except Exception as e:
                        print(f"Failed to add event to calendar for {participant['id']}: {str(e)}")
                        # Continue even if calendar update fails
                
                # Update participant status
                await self.db_service.update_event_participant(
                    request.event_id,
                    request.phone_number,
                    update_data
                )
                
                # Update conversation status
                await self.db_service.update_conversation_status(
                    request.event_id,
                    request.phone_number,
                    participant["name"],
                    "response_received"
                )
                
                # Send confirmation message
                if response_type == "accept":
                    message = "Great! I've added you to the event."
                    if participant["registered"]:
                        message += " I've also added it to your calendar."
                elif response_type == "decline":
                    message = "Thanks for letting me know. I'll update the event accordingly."
                elif response_type == "maybe":
                    message = "Thanks for letting me know. Please confirm your attendance when you can."
                else:  # custom
                    message = "Thanks for your response. I'll make sure the event organizer sees it."
                
                await self.texting_service.send_message(request.phone_number, message)
                
                return {
                    "success": True,
                    "response_type": response_type,
                    "confidence": response.get("confidence", 1.0),
                    "custom_message": response.get("custom_message") if response_type == "custom" else None,
                    "message": message
                }
                
            except Exception as e:
                # If LLM parsing fails, treat as custom response
                print(f"Error parsing response: {str(e)}")
                
                # Update participant status as custom
                update_data = {
                    "status": "custom",
                    "response_text": request.response,
                    "updated_at": datetime.now()
                }
                
                await self.db_service.update_event_participant(
                    request.event_id,
                    request.phone_number,
                    update_data
                )
                
                # Update conversation status
                await self.db_service.update_conversation_status(
                    request.event_id,
                    request.phone_number,
                    participant["name"],
                    "response_received"
                )
                
                # Send generic response
                message = "Thanks for your response. I'll make sure the event organizer sees it."
                await self.texting_service.send_message(request.phone_number, message)
                
                return {
                    "success": True,
                    "response_type": "custom",
                    "confidence": 0.0,
                    "custom_message": request.response,
                    "message": message
                }
            
        except ValueError as e:
            raise OpenRouterError(str(e), 400)
        except Exception as e:
            # Update conversation status to failed
            if conversation:
                await self.db_service.update_conversation_status(
                    request.event_id,
                    request.phone_number,
                    participant["name"],
                    "failed"
                )
            self._handle_error(e, "Failed to handle event response")

    # TODO (NOT FOR MVP)
    async def send_reminder(
        self,
        event_id: str,
        phone_number: str,
        reminder_type: str
    ) -> dict:
        """Sends a day-before or hour-before event reminder to a participant via text message."""
        try:
            # Validate reminder type
            if reminder_type not in ["day_before", "hour_before"]:
                raise RuntimeError(f"Invalid reminder type: {reminder_type}")
                
            # Get event details
            event = await self.db_service.get_event_by_id(event_id)
            if not event:
                raise RuntimeError(f"Event {event_id} not found")
                
            if event["status"] != "scheduled":
                raise RuntimeError(f"Event {event_id} is not scheduled yet")
                
            # Get participant details
            participant = await self.db_service.get_event_participant_by_phone(event_id, phone_number)
            if not participant:
                raise RuntimeError(f"No participant found with phone number {phone_number}")
                
            # Get active invitation conversation
            conversations = await self.db_service.get_conversations(event_id, phone_number)
            conversation = next(
                (c for c in conversations 
                 if c["type"] == "event_invitation" and c["status"] == "response_received"),
                None
            )
            if not conversation:
                raise RuntimeError(
                    f"No active invitation conversation found for {phone_number} - "
                    "send invitation first using send_event_invitation"
                )
                
            # Format the reminder message based on type
            start_time = datetime.fromisoformat(event["final_time"])
            end_time = datetime.fromisoformat(event["end_time"])
            
            if reminder_type == "day_before":
                message = (
                    f"Hi {participant['name']}! Just a friendly reminder about tomorrow's event:\n\n"
                    f"{event['title']}\n"
                    f"Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
                )
                if event.get("location"):
                    message += f"Location: {event['location']}\n"
                message += "\nLooking forward to seeing you there!"
                
            else:  # hour_before
                message = (
                    f"Hi {participant['name']}! Quick reminder that your event starts in an hour:\n\n"
                    f"{event['title']}\n"
                    f"Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
                )
                if event.get("location"):
                    message += f"Location: {event['location']}\n"
                message += "\nSee you soon!"
                
            # Send the reminder
            await self.texting_service.send_message(phone_number, message)
            
            # Create a new conversation for the reminder
            reminder_conversation = await self.db_service.create_conversation(
                event_id,
                phone_number,
                participant["name"],
                "reminder",
                participant.get("id")  # user_id for registered users
            )
            
            # Update conversation status
            await self.db_service.update_conversation_status(
                event_id,
                phone_number,
                participant["name"],
                "reminder_sent"
            )
            
            return {
                "success": True,
                "conversation_id": reminder_conversation["id"],
                "message": message,
                "reminder_type": reminder_type
            }
            
        except Exception as e:
            # Update conversation status to failed
            if conversation:
                await self.db_service.update_conversation_status(
                    event_id,
                    phone_number,
                    participant["name"],
                    "failed"
                )
            self._handle_error(e, "Failed to send reminder")

    # TODO (NOT FOR MVP)
    async def handle_scheduling_conflict(
        self,
        event_id: str,
        participant_phone_numbers: list[str],
        conflict_type: str
    ) -> dict:
        """Handles scheduling conflicts by suggesting alternatives or requesting more availability."""
        try:
            # Validate conflict type
            if conflict_type not in ["no_common_time", "insufficient_availability", "time_preference_conflict"]:
                raise RuntimeError(f"Invalid conflict type: {conflict_type}")
                
            # Get event details
            event = await self.db_service.get_event_by_id(event_id)
            if not event:
                raise RuntimeError(f"Event {event_id} not found")
                
            # Get all participants
            participants = await self.db_service.get_event_participants(event_id)
            if not participants:
                raise RuntimeError(f"No participants found for event {event_id}")
                
            # Filter participants by phone numbers
            target_participants = [
                p for p in participants 
                if p["phone_number"] in participant_phone_numbers
            ]
            if not target_participants:
                raise RuntimeError("No matching participants found for provided phone numbers")
                
            # Get busy times for all participants
            busy_times = await self.db_service.get_all_participants_busy_times(event_id)
            
            # Format messages based on conflict type
            messages = {}
            for participant in target_participants:
                if conflict_type == "no_common_time":
                    message = (
                        f"Hi {participant['name']}! We're having trouble finding a common time for '{event['title']}'. "
                        "Could you please provide more availability options? "
                        "Feel free to suggest any times that work for you."
                    )
                elif conflict_type == "insufficient_availability":
                    message = (
                        f"Hi {participant['name']}! We need more availability options for '{event['title']}'. "
                        "Could you please provide more times when you're free? "
                        "The more options you give, the easier it will be to find a time that works for everyone."
                    )
                else:  # time_preference_conflict
                    message = (
                        f"Hi {participant['name']}! There seems to be a conflict in time preferences for '{event['title']}'. "
                        "Could you please provide some alternative times that might work for you? "
                        "We're trying to accommodate everyone's schedules."
                    )
                
                messages[participant["phone_number"]] = message
                
            # Send messages and create conversations
            conversation_results = []
            for participant in target_participants:
                try:
                    # Send the message
                    await self.texting_service.send_message(
                        participant["phone_number"],
                        messages[participant["phone_number"]]
                    )
                    
                    # Create a new conversation for the conflict resolution
                    conversation = await self.db_service.create_conversation(
                        event_id,
                        participant["phone_number"],
                        participant["name"],
                        "availability_request",  # Reuse availability request type
                        participant.get("id")  # user_id for registered users
                    )
                    
                    # Update conversation status
                    await self.db_service.update_conversation_status(
                        event_id,
                        participant["phone_number"],
                        participant["name"],
                        "needs_rescheduling"
                    )
                    
                    conversation_results.append({
                        "participant_id": participant["id"],
                        "phone_number": participant["phone_number"],
                        "status": "sent",
                        "conversation_id": conversation["id"]
                    })
                    
                except Exception as e:
                    conversation_results.append({
                        "participant_id": participant["id"],
                        "phone_number": participant["phone_number"],
                        "status": "failed",
                        "error": str(e)
                    })
            
            # Update event status
            await self.db_service.update_event(
                event_id,
                {"status": "needs_rescheduling"}
            )
            
            return {
                "success": True,
                "event_id": event_id,
                "conflict_type": conflict_type,
                "conversations": conversation_results
            }
            
        except Exception as e:
            self._handle_error(e, "Failed to handle scheduling conflict")

    # TODO: SEND_EVENT_UPDATE_TOOL
    # - Send updates about event changes
    # - Parameters: phone_number, event_id, update_type (time/location/participants)
    # - Different templates based on update type
    # - Updates conversation status to "update_sent"

    # TODO: HANDLE_UPDATE_RESPONSE_TOOL
    # - Process responses to event updates
    # - Parameters: phone_number, response_text
    # - Updates participant status based on response
    # - Updates conversation status accordingly

    async def send_event_invitation(
        self,
        event_id: str,
        phone_number: str,
        include_ics: bool = True
    ) -> dict:
        """Sends an event invitation text message to a participant, with optional ICS calendar file for registered users."""
        try:
            # Get event details
            event = await self.db_service.get_event_by_id(event_id)
            if not event:
                raise RuntimeError(f"Event {event_id} not found")
                
            if event["status"] != "scheduled":
                raise RuntimeError(f"Event {event_id} is not scheduled yet")
                
            # Get participant details
            participant = await self.db_service.get_event_participant_by_phone(event_id, phone_number)
            if not participant:
                raise RuntimeError(f"No participant found with phone number {phone_number}")
                
            # Get active invitation conversation
            conversations = await self.db_service.get_conversations(event_id, phone_number)
            conversation = next(
                (c for c in conversations 
                 if c["type"] == "event_invitation" and c["status"] == "active"),
                None
            )
            if not conversation:
                raise RuntimeError(
                    f"No active invitation conversation found for {phone_number} - "
                    "create conversation first using schedule_event"
                )
                
            # Format the invitation message
            start_time = datetime.fromisoformat(event["final_time"])
            end_time = datetime.fromisoformat(event["end_time"])
            
            if participant["registered"]:
                # For registered users, include more details and ICS file
                message = (
                    f"Hi {participant['name']}!\n\n"
                    f"You're invited to: {event['title']}\n"
                    f"Date: {start_time.strftime('%A, %B %d, %Y')}\n"
                    f"Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
                )
                
                if event.get("location"):
                    message += f"Location: {event['location']}\n"
                    
                if event.get("description"):
                    message += f"\nDetails: {event['description']}\n"
                    
                message += "\nPlease reply with 'yes' to accept or 'no' to decline."
                
                # Generate and attach ICS file if requested
                if include_ics:
                    ics_content = self.google_calendar_service.generate_ics(
                        event["title"],
                        event["final_time"],
                        event["end_time"],
                        event.get("location"),
                        event.get("description")
                    )
                    # Send ICS file as MMS
                    await self.texting_service.send_mms(
                        phone_number,
                        message,
                        ics_content,
                        "calendar.ics"
                    )
                else:
                    # Send text-only invitation
                    await self.texting_service.send_message(phone_number, message)
                    
            else:
                # For unregistered users, keep it simple
                message = (
                    f"Hi {participant['name']}!\n\n"
                    f"You're invited to: {event['title']}\n"
                    f"Date: {start_time.strftime('%A, %B %d, %Y')}\n"
                    f"Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
                )
                
                if event.get("location"):
                    message += f"Location: {event['location']}\n"
                    
                message += "\nPlease reply with 'yes' to accept or 'no' to decline."
                
                # Send text-only invitation
                await self.texting_service.send_message(phone_number, message)
                
            # Update conversation status
            await self.db_service.update_conversation_status(
                event_id,
                phone_number,
                participant["name"],
                "invitation_sent"
            )
            
            return {
                "success": True,
                "conversation_id": conversation["id"],
                "message": message,
                "ics_included": include_ics and participant["registered"]
            }
            
        except Exception as e:
            # Update conversation status to failed
            if conversation:
                await self.db_service.update_conversation_status(
                    event_id,
                    phone_number,
                    participant["name"],
                    "failed"
                )
            self._handle_error(e, "Failed to send event invitation")