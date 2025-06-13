import os
import requests
import json
from typing import Optional, Dict, List, Any
from .tools import AVAILABLE_TOOLS, TOOL_INDICES
from app.services.database_service import DatabaseService
from app.core.config import settings
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.services.texting_service import TextingService
from app.services.websocket_service import send_chat_message
from uuid import uuid4, UUID
from app.models.time_slot import TimeSlot
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import logging
from pydantic import BaseModel, Field, validator
from app.services.prompts import AVAILABLE_PROMPTS
import asyncio
from openai import OpenAI

API_URL = "https://openrouter.ai/api/v1"
MODEL = "qwen/qwen-turbo"

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
        texting_service: TextingService = None
    ):
        self.api_url = API_URL
        self.model = MODEL
        self.api_key = settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set in environment")
        self._current_event_id: Optional[str] = None
        self._current_owner_id: Optional[str] = None
        self._current_participants: Optional[dict[str, dict]] = None  # Dict of phone_number -> participant for current event
        self.db_service = db_service
        self.google_calendar_service = google_calendar_service
        self.token_manager = token_manager
        self.texting_service = texting_service
        self.available_tools = AVAILABLE_TOOLS
        self.stage_number = 0

        self.TOOL_MAPPINGS = {
            "create_draft_event": self.create_draft_event,
            "search_contacts": self.search_contacts,
            "check_user_registration": self.check_user_registration,
            "create_event_participant": self.create_event_participant,
            "create_or_get_conversation": self.create_or_get_conversation,
            "handle_confirmation": self.handle_confirmation,
            "send_text": self.send_text,
            "get_google_calendar_busy_times": self.get_google_calendar_busy_times,
            "get_creator_google_calendar_busy_times": self.get_google_calendar_busy_times,
            "create_unregistered_time_slots": self.create_unregistered_time_slots,
            "create_final_time_slots": self.create_final_time_slots,
            "schedule_event": self.schedule_event,
            "send_event_invitation": self.send_event_invitation,
            "handle_scheduling_conflict": self.handle_scheduling_conflict,
            "send_chat_message_to_user": self.send_chat_message_to_user,
            "get_event_availabilities": self.get_event_availabilities,
            "stop_loop": self.stop_loop
        }

    @property
    def current_event_id(self) -> Optional[str]:
        # Get the ID of the event currently being worked on
        return self._current_event_id

    def set_current_event(self, event_id: str) -> None:
        # Set the ID of the event currently being worked on
        self._current_event_id = event_id
        self._current_participants = None  # Clear cached participants

    def clear_current_event(self) -> None:
        # Clear the current event ID and related data
        self._current_event_id = None
        self._current_owner_id = None
        self._current_participants = None

    async def _get_current_participants(self) -> dict[str, dict]:
        """Get participants for current event, using cache if available.
        Returns a dictionary mapping phone numbers to participant data."""
        if not self.current_event_id:
            raise RuntimeError("No current event set")
            
        if self._current_participants is None:
            # Get participants from database
            participants_list = await self.db_service.get_event_participants(self.current_event_id)
            # Convert to dictionary with phone numbers as keys
            self._current_participants = {
                p["phone_number"]: p for p in participants_list
            }
            
        return self._current_participants

    def _handle_error(self, error: Exception, context: str) -> None:
        """Standardized error handling for the service"""
        if isinstance(error, OpenRouterError):
            logger.error(f"{context}: {error.message}")
            raise HTTPException(status_code=error.status_code, detail=error.message)
        else:
            logger.error(f"{context}: Unexpected error: {str(error)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    async def prompt_agent(self, messages: list[dict[str, str]], tools: list[dict[str, Any]]) -> tuple[Dict[str, Any], Dict[str, int]]:
        """Send a prompt to the OpenRouter agent and get a response"""
        try:         
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools
            )
            return response.choices[0].message, response.usage
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {str(e)}")
            raise RuntimeError(f"Failed to communicate with OpenRouter API: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing OpenRouter response: {str(e)}")
            raise RuntimeError(f"Failed to process OpenRouter response: {str(e)}")

    async def create_draft_event(self, creator_id: UUID, title: str, description: Optional[str] = None) -> dict:
        """Create a draft event"""
        try:
            event = await self.db_service.create_draft_event(creator_id, title, description)
            self.set_current_event(event["id"])
            self._current_owner_id = creator_id  # Store the registered user's ID
            return event
        except Exception as e:
            self._handle_error(e, "Failed to create draft event")

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
            print("No current owner set - create an event first")
            raise RuntimeError("No current owner set - create an event first")
        
        return await self.db_service.search_contacts(
            self._current_owner_id,  # Use the registered user's ID to find their contacts
            query,
            min_relationship_score,
            recent_only,
            limit,
            days_ago
        )
    
    async def check_user_registration(self, phone_number: str, name: str = None) -> dict:
        """Check if a phone number belongs to a registered user and return their registration details and Google Calendar access status."""
        try:
            # Check if user exists in database
            user = await self.db_service.get_user_by_phone(phone_number)
            
            if not user:
                return {
                    "is_registered": False,
                    "user_id": None,
                    "owner_id": self._current_owner_id,
                    "name": name,
                    "phone_number": phone_number,
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
                "name": user["name"],  # Use registered user's name from database
                "owner_id": self._current_owner_id,
                "phone_number": phone_number,
                "has_google_calendar": has_google_calendar
            }
            
        except Exception as e:
            raise RuntimeError(f"Error checking user registration: {str(e)}")
        
    async def create_event_participant(
        self,
        phone_number: str,
        name: str
    ) -> dict:
        # Create a participant for the current event
        if not self.current_event_id:
            raise RuntimeError("No current event set")
            
        # Check if participant already exists
        existing_participant = await self.db_service.get_event_participant_by_phone(
            self.current_event_id,
            phone_number
        )
        if existing_participant:
            return existing_participant
            
        participant = await self.db_service.create_event_participant(
            self.current_event_id,
            phone_number,
            name
        )
        
        # Update cache if it exists
        if self._current_participants is not None:
            self._current_participants[phone_number] = participant
            
        return participant

    async def create_or_get_conversation(
        self,
        phone_number: str,
        user_name: str,
        user_id: str = None,
    ) -> dict:
        """Each person (identified by phone number) will only ever have one conversation."""
        if not self.current_event_id:
            print("No current event set - create an event first")
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching one
        participants = await self._get_current_participants()
        participant = participants.get(phone_number)
        print(f"Participant: {participant}")
        if not participant:
            print(f"No participant found with phone number {phone_number} - create participant first using create_event_participant")
            raise RuntimeError(
                f"No participant found with phone number {phone_number} - "
                "create participant first using create_event_participant"
            )
            
        # Verify participant registration status matches user_id
        if user_id and not participant["registered"]:
            print(f"Participant {phone_number} is not registered but user_id was provided")
            raise RuntimeError(
                f"Participant {phone_number} is not registered but user_id was provided"
            )
        if not user_id and participant["registered"]:
            print(f"Participant {phone_number} is registered but no user_id was provided")
            raise RuntimeError(
                f"Participant {phone_number} is registered but no user_id was provided"
            )
        
        # # Get conversation if exists
        # conversation = await self.db_service.get_conversation_by_phone(phone_number)
        # if conversation:
        #     ...
        # else:
        # Create conversation for this availability request
        conversation = await self.db_service.create_conversation(
            self.current_event_id,
            phone_number,
            user_name,
            "registered" if user_id else "unregistered",
            user_id
        )
        
        return {
            "success": True,
            "conversation": conversation,
            "phone_number": phone_number
        }

    async def handle_confirmation(
        self,
        phone_number: str,
        confirmation: bool,
        message: str
    ) -> dict:
        """Update conversation and participant status based on user's confirmation response."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching one
        participants = await self._get_current_participants()
        participant = participants.get(phone_number)
        if not participant:
            raise RuntimeError(f"No participant found with phone number {phone_number}")
            
        # Get active conversation
        conversations = await self.db_service.get_conversations(
            self.current_event_id,
            phone_number
        )
        conversation = next(
            (c for c in conversations 
             if c["type"] in ["registered", "unregistered"] and c["status"] == "active"),
            None
        )
        if not conversation:
            raise RuntimeError(
                f"No active conversation found for {phone_number} - "
                "create conversation first using create_availability_conversation"
            )
            
        # Update participant status
        now = datetime.now()
        update_data = {
            "status": "pending_availability" if confirmation else "declined", 
            "response_text": message,
            "updated_at": now.isoformat(),
        }
        
        await self.db_service.update_event_participant(
            self.current_event_id,
            phone_number,
            update_data
        )
        
        # Update cache if it exists
        if self._current_participants is not None:
            self._current_participants[phone_number].update(update_data)
            
        # Update conversation status
        if confirmation:
            await self.db_service.update_conversation(
                self.current_event_id,
                phone_number,
                "active"
            )
            now = datetime.now()
            update_data = {
                "status": "pending_availability", 
                "response_text": message,
                "updated_at": now.isoformat(),
            }
            print(f"Updating event participant to pending_availability: {update_data}")
            await self.db_service.update_event_participant(
                self.current_event_id,
                phone_number,
                update_data
            )
            self._current_participants[phone_number].update(update_data)
        else:
            await self.db_service.update_conversation(
                self.current_event_id,
                phone_number,
                "active"
            )
            now = datetime.now()
            update_data = {
                "status": "declined", 
                "response_text": message,
                "updated_at": now.isoformat(),
            }
            await self.db_service.update_event_participant(
                self.current_event_id,
                phone_number,
                update_data
            )
            self._current_participants[phone_number].update(update_data)
        return {
            "success": True,
            "confirmation": confirmation,
            "message": message
        }

    async def send_text(
        self,
        phone_number: str,
        message: str,
        final: bool = False
    ) -> dict:
        """Send a text message to a user."""
        try:
            # Get active conversation
            conversations = await self.db_service.get_conversations(self.current_event_id, phone_number)
            active_conversation = next(
                (c for c in conversations if c["status"] == "active"),
                None
            )
            
            # Send the message
            await self.texting_service.send_text(phone_number, message, final=final)

            # Update last message in conversation
            if active_conversation:
                await self.db_service.update_conversation(
                    self.current_event_id,
                    phone_number,
                    "active",
                    active_conversation["user_name"],
                    last_message=message
                )
            
            return {
                "success": True,
                "message": message,
                "final": final
            }
        except Exception as e:
            raise RuntimeError(f"Failed to send message: {str(e)}")

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
            print(f"User {user_id} not found or not registered with Google Calendar")
            raise RuntimeError(f"User {user_id} not found or not registered with Google Calendar")
        print(f"Tokens: {tokens}")
        # Get events from Google Calendar
        events = await self.google_calendar_service.get_all_events(
            tokens['google_access_token'],
            start_date,
            end_date
        )
        print(f"Events: {events}")
        
        # Convert events to busy time slots
        busy_slots = []
        for event in events:
            # Skip events that are marked as free
            busy_slots.append({
                "id": str(uuid4()),
                "participant_id": user_id,
                "start_time": event['start'],  # Now a string
                "end_time": event['end'],      # Now a string
                "source": "calendar"
            })
        print(f"Busy slots: {busy_slots}")
        # Store the busy times in the database
        await self.db_service.store_participant_busy_times(
            self.current_event_id,
            user_id,
            busy_slots
        )
            
        return busy_slots
    
    async def create_unregistered_time_slots(
        self,
        phone_number: str,
        time_slots: list[dict]
    ) -> list[dict]:
        """Store time slots for an unregistered user based on their text responses."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Validate time slots
        for slot in time_slots:
            if not isinstance(slot.get("start_time"), str) or not isinstance(slot.get("end_time"), str):
                raise ValueError("Time slots must have string start_time and end_time")
            try:
                start = datetime.fromisoformat(slot["start_time"])
                end = datetime.fromisoformat(slot["end_time"])
                if end <= start:
                    raise ValueError("End time must be after start time")
            except ValueError as e:
                raise ValueError(f"Invalid time format in slot: {e}")
            
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
        if not any(c["type"] == "unregistered" and c["status"] == "active" 
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
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                slot_type=slot["slot_type"],
                source="text"
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
            await self.db_service.update_conversation(
                self.current_event_id,
                phone_number,
                "active"
            )
        
        return formatted_slots

    async def schedule_event(
        self,
        event_id: str,
        start: dict,
        end: dict,
        location: str = None,
        creator_message: str = None
    ) -> dict:
        """Schedule event with final details and notify participants. Returns updated event info and notification status."""
        try:
            # Validate the event exists and get its details
            print(f"Start: {start}")
            print(f"End: {end}")
            event = await self.db_service.get_event_by_id(event_id)
            if not event:
                raise RuntimeError(f"Event {event_id} not found")
                
            # Get all participants
            participants = await self.db_service.get_event_participants(event_id)
            print(f"Participants: {participants}")
            # Send notifications to all participants
            attendees = []
            for participant in participants:
                await self.db_service.update_conversation(
                        event_id,
                        participant["phone_number"],
                        "completed"
                    )
                if participant["status"] != "declined":
                    if participant["registered"]: # only registered users have a calendarId
                        user = await self.db_service.get_user_by_phone(participant["phone_number"])
                        attendees.append(user)
            print(f"Attendees: {attendees}")
            creator = await self.db_service.get_user_by_id(event["creator_id"])
            print(f"Creator: {creator}")

            access_token = await self.token_manager.get_token(creator["id"])


            await self.google_calendar_service.add_event(
                access_token["google_access_token"],
                event["title"],
                start,
                end,
                attendees=attendees,
                location=location,
                description=event["description"]
            )
            print("added event to google calendar")

            for attendee in attendees:
                access_token = await self.token_manager.get_token(attendee["id"])
                await self.google_calendar_service.add_event(
                    access_token["google_access_token"],
                    event["title"],
                    start,
                    end,
                    attendees=[attendee],
                    location=location,
                    description=event["description"]
                )
            # Update event with final details
            update_data = {
                "status": "scheduled",
                "final_start": start,
                "final_end": end,
                "location": location
            }
            print(f"Updating event: {update_data}")
            updated_event = await self.db_service.update_event(event_id, update_data)
            print(f"Updated event: {updated_event}")

            # Send final message to creator via chat
            final_message = f"Great! Your event '{event['title']}' has been scheduled for {start['dateTime']} - {end['dateTime']}"
            if location:
                final_message += f" at {location}"
            final_message += "."
            print(f"Sending final message to creator: {final_message}")
            if creator_message:
                final_message = creator_message
            await self.send_chat_message_to_user(creator["id"], final_message)

            # Send text messages to participants
            for participant in participants:
                if participant["status"] == "confirmed": # only confirmed participants
                    await self.send_text(
                        participant["phone_number"],
                        f"Scheduled {event['title']} with {creator['name']} for {start['dateTime']} - {end['dateTime']} at {location}.",
                        final=True
                    )
                    print(f"Sent final message to participant: {participant['phone_number']}")
            return {
                "success": True,
                "event": updated_event,
                "creator_message": creator_message
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to schedule event: {str(e)}")

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
            await self.send_text(phone_number, message)
            
            # Create a new conversation for the reminder
            reminder_conversation = await self.db_service.create_conversation(
                event_id,
                phone_number,
                participant["name"],
                "reminder",
                participant.get("id")  # user_id for registered users
            )
            
            # Update conversation status
            await self.db_service.update_conversation(
                event_id,
                phone_number,
                "active",
                participant["name"],
                last_message=message
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
                await self.db_service.update_conversation(
                    event_id,
                    phone_number,
                    "active",
                    participant["name"]
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
                    await self.send_text(
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
                    await self.db_service.update_conversation(
                        event_id,
                        participant["phone_number"],
                        participant["name"],
                        "active"
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

    # TODO: NOT FOR MVP
    async def send_event_invitation(
        self,
        event_id: str,
        phone_number: str,
        include_ics: bool = True
    ) -> dict:
        """Sends an event invitation text message to a participant, with optional ICS calendar file for registered users."""
        conversation = None
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
                    await self.send_text(phone_number, message)
                    
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
                await self.send_text(phone_number, message)
                
            # Update conversation status
            await self.db_service.update_conversation(
                event_id,
                phone_number,
                "active",
                participant["name"]
            )
            
            return {
                "success": True,
                "conversation_id": conversation["id"],
                "message": message,
                "ics_included": include_ics and participant["registered"]
            }
            
        except Exception as e:
            # Update conversation status to failed if we have a conversation
            if conversation and participant:
                await self.db_service.update_conversation(
                    event_id,
                    phone_number,
                    "active",
                    participant["name"]
                )
            self._handle_error(e, "Failed to send event invitation")

    # TODO: NOT FOR MVP
    async def create_final_time_slots(
        self,
        phone_number: str,
        time_slots: list[dict],
        user_id: str = None
    ) -> dict:
        """Create and store final time slots once sufficient availability information has been collected."""
        if not self.current_event_id:
            raise RuntimeError("No current event set - create an event first")
            
        # Get all event participants and find the matching one
        participants = await self._get_current_participants()
        participant = participants.get(phone_number)
        if not participant:
            raise RuntimeError(f"No participant found with phone number {phone_number}")
            
        # Get active conversation
        conversations = await self.db_service.get_conversations(
            self.current_event_id,
            phone_number
        )
        conversation = next(
            (c for c in conversations 
             if c["type"] in ["registered", "unregistered"] and c["status"] == "active"),
            None
        )
        if not conversation:
            raise RuntimeError(
                f"No active availability conversation found for {phone_number} - "
                "user must confirm interest first using parse_confirmation"
            )
            
        # For registered users, store in participant_busy_times
        if user_id:
            await self.db_service.store_participant_busy_times(
                self.current_event_id,
                user_id,
                time_slots
            )
        else:
            # For unregistered users, store in unregistered_time_slots
            await self.db_service.store_unregistered_time_slots(
                self.current_event_id,
                phone_number,
                time_slots
            )
            
        # Update conversation status to completed
        await self.db_service.update_conversation(
            self.current_event_id,
            phone_number,
            "active"
        )
            
        return {
            "success": True,
            "time_slots": time_slots
        }
    
    async def send_chat_message_to_user(self, user_id: str, message: str) -> dict:
        """Send a chat message to the user via WebSocket if more information is needed."""
        await send_chat_message(user_id, message)
        return {"success": True, "message": message}
    
    async def get_event_availabilities(self, event_id: str) -> dict:
        # Add availability information
        busy_times = await self.db_service.get_all_participants_busy_times(event_id)
        unregistered_time_slots = await self.db_service.get_all_unregistered_time_slots(event_id)
        return {
            "busy_times": busy_times,
            "unregistered_time_slots": unregistered_time_slots
        }
    
    async def stop_loop(self):
        return True

    TOOLS_FOR_STAGE = {
        "agent_loop": [
            "create_draft_event",
            "search_contacts",
            "check_user_registration",
            "create_event_participant",
            "create_or_get_conversation",
            "send_text",
            "get_creator_google_calendar_busy_times",
            "send_chat_message_to_user",
            "stop_loop"
        ],
        "confirmation": [
            "handle_confirmation",
            "send_text",
            "send_chat_message_to_user",
            "stop_loop"
        ],
        "availability": [
            "get_google_calendar_busy_times",
            "create_unregistered_time_slots",
            "create_final_time_slots",
            "send_text",
            "send_chat_message_to_user",
            "stop_loop"
        ],
        "scheduling": [
            "get_event_availabilities",
            "schedule_event",
            "send_text",
            "send_chat_message_to_user",
            "stop_loop"
        ]
    }

    async def run_agent_loop(self, user_input: str, creator_id: str, stage_limit=2, stage_idx=0, max_steps=10):
        """Run the agent loop for event creation and scheduling.
        
        Args:
            user_input: Initial user input
            creator_id: ID of the event creator
            stage_limit: Maximum number of stages to process
            stage_idx: Starting stage index
        """
        print("running agent loop")
        messages = []  # Messages to be sent to the agent
        phone_numbers = set()  # Track phone numbers involved
        response = None  # Last response from agent
        step = 0  # Step counter
        self._current_owner_id = creator_id
        tool_call_history = []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        # Get creator details
        creator = await self.db_service.get_user_by_id(creator_id)
        creator_name = creator["name"] if creator else "A friend"

        # Get current datetime in ISO format with timezone
        current_datetime = datetime.now().astimezone().isoformat()

        while stage_idx < stage_limit and step < max_steps:
            try:
                # Get tools for current stage
                stage = self.STAGES[stage_idx]
                tools = [
                    AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                    for tool_name in self.TOOLS_FOR_STAGE[stage] 
                    if tool_name in self.TOOL_MAPPINGS
                ]

                # Prepare messages
                if step == 0:
                    messages = [
                        {
                            "role": "system",
                            "content": f"""You are an AI assistant helping to create and schedule events.
                            Current datetime: {current_datetime}
                            Creator ID: {creator_id}
                            Creator Name: {creator_name}
                            
                            {AVAILABLE_PROMPTS[stage].format(current_datetime=current_datetime)}"""
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ]
                else:
                    # Add tool call results to messages
                    if response and hasattr(response, 'tool_calls'):
                        for tool_call in response.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
                            if tool_name in self.TOOL_MAPPINGS:
                                try:
                                    print("<<<<<<<<<<<<<<<<<<<<")
                                    print("tool_name", tool_name)
                                    print("tool_args", tool_args)
                                    result = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                                    print("result", result)
                                    print(">>>>>>>>>>>>>>>>>>>>>")
                                    messages.append({
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": [{
                                            "id": str(uuid4()),
                                            "type": "function",
                                            "function": {
                                                "name": tool_name,
                                                "arguments": json.dumps(tool_args)
                                            }
                                        }]
                                    })
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": str(uuid4()),
                                        "content": json.dumps(result)
                                    })
                                    
                                    # Track phone numbers from tool calls
                                    if "phone_number" in tool_args:
                                        phone_numbers.add(tool_args["phone_number"])
                                        
                                    # Check if we should stop the loop
                                    if tool_name == "stop_loop":
                                        return {
                                            "success": True,
                                            "phone_numbers": list(phone_numbers),
                                            "tool_call_history": tool_call_history,
                                            "total_prompt_tokens": total_prompt_tokens,
                                            "total_completion_tokens": total_completion_tokens
                                        }
                                        
                                except Exception as e:
                                    logger.error(f"Error executing tool {tool_name}: {str(e)}")
                                    messages.append({
                                        "role": "assistant",
                                        "content": f"Error executing {tool_name}: {str(e)}"
                                    })
                                    continue

                # Get response from agent
                print("====================")
                print("messages", messages)
                print("====================")
                response, usage = await self.prompt_agent(messages, tools)
                print("====================")
                print("response", response)
                print("====================")
                total_prompt_tokens += usage.get("prompt_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0)

                # Track tool calls
                if hasattr(response, 'tool_calls'):
                    for tool_call in response.tool_calls:
                        tool_call_history.append({
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments)
                        })

                step += 1

            except Exception as e:
                logger.error(f"Error in agent loop: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "phone_numbers": list(phone_numbers),
                    "tool_call_history": tool_call_history,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens
                }

        return {
            "success": True,
            "phone_numbers": list(phone_numbers),
            "tool_call_history": tool_call_history,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens
        }

    async def handle_inbound_message(self, phone_number: str, message: str) -> dict:
        """Handle an incoming text message from a participant.
        
        Args:
            phone_number: The phone number of the sender
            message: The message content
            
        Returns:
            dict: Response containing message details and any additional data
        """
        try:
            # Find active conversation for this phone number
            conversations = await self.db_service.get_conversations_by_phone(phone_number)
            active_conversation = next(
                (c for c in conversations if c["status"] == "active"),
                None
            )
            
            if not active_conversation:
                logger.warning(f"No active conversation found for {phone_number}")
                return {"message": message, "from_number": phone_number}
            
            # Set the current event from the conversation
            self.set_current_event(active_conversation["event_id"])
            
            # Get event and participant details
            now = datetime.now()
            current_datetime = now.astimezone().isoformat()
            event = await self.db_service.get_event_by_id(active_conversation["event_id"])
            participant = await self.db_service.get_event_participant_by_phone(active_conversation["event_id"], phone_number)
            
            if not participant:
                logger.error(f"No participant found for event {active_conversation['event_id']} and phone {phone_number}")
                return {"message": message, "from_number": phone_number}

            creator = await self.db_service.get_user_by_id(event["creator_id"])
            creator_name = creator["name"] if creator else "A friend"

            # Build context for the agent
            context = f"""Event: {event["title"]}
                \nEvent ID: {event["id"]}
                \nOwner ID: {event["creator_id"]}
                \nOwner Name: {creator_name}
                \nPhone number: {phone_number}
                \nLast message sent to user: {active_conversation.get("last_message", "No previous message")}
                \nParticipant status: {participant["status"]}
                \nUser replied: {message}
                """
            
            # Handle different participant statuses
            if participant["status"] == "pending_confirmation":
                # Handle confirmation response
                messages = [
                    {
                        "role": "system",
                        "content": AVAILABLE_PROMPTS["confirmation"].format(current_datetime=current_datetime)
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ]
                tools = [
                    AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                    for tool_name in self.TOOLS_FOR_STAGE["confirmation"] 
                    if tool_name in self.TOOL_MAPPINGS
                ]
                
                response, usage = await self.prompt_agent(messages, tools)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        if tool_name in self.TOOL_MAPPINGS:
                            await self.TOOL_MAPPINGS[tool_name](**tool_args)
                
                # After handling confirmation, check if we need to move to availability
                participant = await self.db_service.get_event_participant_by_phone(active_conversation["event_id"], phone_number)
                if participant["status"] == "pending_availability":
                    if participant["registered"]:
                        # Handle registered user availability
                        context += f"\nParticipant ID: {participant['user_id']}"
                        messages = [
                            {
                                "role": "system",
                                "content": AVAILABLE_PROMPTS["availability"].format(current_datetime=current_datetime)
                            },
                            {
                                "role": "user",
                                "content": context
                            }
                        ]
                        tools = [
                            AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                            for tool_name in self.TOOLS_FOR_STAGE["availability"] 
                            if tool_name in self.TOOL_MAPPINGS
                        ]
                        
                        response, usage = await self.prompt_agent(messages, tools)
                        
                        if hasattr(response, 'tool_calls') and response.tool_calls:
                            for tool_call in response.tool_calls:
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)
                                
                                if tool_name in self.TOOL_MAPPINGS:
                                    await self.TOOL_MAPPINGS[tool_name](**tool_args)
                        
                        # Update participant status
                        update_data = {
                            "status": "pending_scheduling",
                            "response_text": message,
                            "updated_at": now.isoformat(),
                        }
                        await self.db_service.update_event_participant(
                            self._current_event_id,
                            phone_number,
                            update_data
                        )
                        if self._current_participants:
                            self._current_participants[phone_number].update(update_data)
                            
                    else:
                        # Handle unregistered user availability
                        messages = [
                            {
                                "role": "system",
                                "content": AVAILABLE_PROMPTS["availability"].format(current_datetime=current_datetime)
                            },
                            {
                                "role": "user",
                                "content": context
                            }
                        ]
                        tools = [
                            AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                            for tool_name in self.TOOLS_FOR_STAGE["availability"] 
                            if tool_name in self.TOOL_MAPPINGS
                        ]
                        
                        response, usage = await self.prompt_agent(messages, tools)
                        
                        if hasattr(response, 'tool_calls') and response.tool_calls:
                            for tool_call in response.tool_calls:
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)
                                
                                if tool_name in self.TOOL_MAPPINGS:
                                    await self.TOOL_MAPPINGS[tool_name](**tool_args)
                
            elif participant["status"] == "pending_availability":
                # Handle availability response
                messages = [
                    {
                        "role": "system",
                        "content": AVAILABLE_PROMPTS["availability"].format(current_datetime=current_datetime)
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ]
                tools = [
                    AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                    for tool_name in self.TOOLS_FOR_STAGE["availability"] 
                    if tool_name in self.TOOL_MAPPINGS
                ]
                
                response, usage = await self.prompt_agent(messages, tools)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        if tool_name in self.TOOL_MAPPINGS:
                            await self.TOOL_MAPPINGS[tool_name](**tool_args)
                
                # Update participant status
                update_data = {
                    "status": "pending_scheduling",
                    "response_text": message,
                    "updated_at": now.isoformat(),
                }
                await self.db_service.update_event_participant(
                    self._current_event_id,
                    phone_number,
                    update_data
                )
                
                # Check if all participants are ready for scheduling
                participants = await self.db_service.get_event_participants(self._current_event_id)
                if all(p["status"] == "pending_scheduling" for p in participants):
                    # Get all participant times
                    participant_times = {}
                    for p in participants:
                        if p["registered"]:
                            participant_times[p["name"]] = await self.db_service.get_participant_busy_times(
                                self._current_event_id,
                                p["user_id"]
                            )
                        else:
                            participant_times[p["name"]] = await self.db_service.get_unregistered_time_slots(
                                self._current_event_id,
                                p["phone_number"]
                            )
                    
                    # Get creator times
                    creator_times = await self.db_service.get_participant_busy_times(
                        self._current_event_id,
                        event["creator_id"]
                    )
                    
                    # Add times to context
                    context += f"\nParticipant times: {participant_times}"
                    context += f"\nCreator times: {creator_times}"
                    
                    # Schedule event
                    messages = [
                        {
                            "role": "system",
                            "content": AVAILABLE_PROMPTS["scheduling"].format(current_datetime=current_datetime)
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ]
                    tools = [
                        AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                        for tool_name in self.TOOLS_FOR_STAGE["scheduling"] 
                        if tool_name in self.TOOL_MAPPINGS
                    ]
                    
                    response, usage = await self.prompt_agent(messages, tools)
                    
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        creator_message = None
                        for tool_call in response.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
                            if tool_name in self.TOOL_MAPPINGS:
                                result = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                                if tool_name == "schedule_event":
                                    creator_message = result.get("creator_message")
                        
                        # Update participant status to confirmed
                        update_data = {
                            "status": "confirmed",
                            "response_text": message,
                            "updated_at": now.isoformat(),
                        }
                        await self.db_service.update_event_participant(
                            self._current_event_id,
                            phone_number,
                            update_data
                        )
                        if self._current_participants:
                            self._current_participants[phone_number].update(update_data)
                        
                        return {
                            "message": message,
                            "from_number": phone_number,
                            "creator_message": creator_message
                        }
            
            elif participant["status"] in ["confirmed", "declined"]:
                return {"message": message, "from_number": phone_number}
            
            return {"message": message, "from_number": phone_number}
            
        except Exception as e:
            logger.error(f"Error processing inbound message: {str(e)}")
            # Keep conversation active if there's an error
            if active_conversation:
                await self.db_service.update_conversation(
                    active_conversation["event_id"],
                    phone_number,
                    "active",
                    active_conversation["user_name"]
                )
            return {"message": message, "from_number": phone_number}

    async def handle_chat_request(self, request: dict) -> dict:
        """Handle a chat request from the user.
        
        Args:
            request: Dictionary containing:
                - request: The user's message
                - creator_id: ID of the user making the request
                
        Returns:
            Dictionary containing the response
        """
        try:
            message = request.get("request")
            creator_id = request.get("creator_id")
            
            if not creator_id or not message:
                raise ValueError("creator_id and request are required")
                
            # Get or create chat session
            chat_session = await self.db_service.get_or_create_chat_session(creator_id)
            
            # Add user message to session
            await self.db_service.extend_chat_session_message(
                chat_session["id"],
                [{"role": "user", "content": message}]
            )
            
            # Get last K messages for context
            messages = await self.db_service.get_last_k_chat_session_messages(chat_session["id"])
            
            # Get tools based on whether this is an event-related chat
            tools = []
            if "event_id" in request:
                # If this is an event chat, get tools for the current event stage
                event = await self.db_service.get_event_by_id(request["event_id"])
                if event:
                    stage = self.STAGES[event["stage"]]
                    tools = [
                        AVAILABLE_TOOLS[TOOL_INDICES[tool_name]] 
                        for tool_name in self.TOOLS_FOR_STAGE[stage] 
                        if tool_name in self.TOOL_MAPPINGS
                    ]
            
            # Get response from OpenRouter
            response, usage = await self.prompt_agent(messages, tools)
            
            # Add assistant response to session
            await self.db_service.extend_chat_session_message(
                chat_session["id"],
                [{"role": "assistant", "content": response.content}]
            )
            
            return {
                "success": True,
                "response": response.content,
                "usage": usage
            }
            
        except Exception as e:
            logger.error(f"Error handling chat request: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process chat request: {str(e)}"
            )
