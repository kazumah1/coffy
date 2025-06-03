import os
import requests
import json
from typing import Optional, Dict, List, Any
from .tools import AVAILABLE_TOOLS, TOOL_NAME_TO_INDEX
from app.services.database_service import DatabaseService
from app.core.config import settings
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.services.texting_service import TextingService
from app.services.websocket_service import send_chat_message
from uuid import uuid4, UUID
from app.models.time_slot import TimeSlot
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging
from pydantic import BaseModel, Field, validator
from app.services.prompts import AVAILABLE_PROMPTS
import asyncio
from openai import OpenAI

API_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemini-2.0-flash-001"

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
            "send_confirmation_text": self.send_confirmation_text,
            "send_availability_text": self.send_availability_text,
            "send_final_text": self.send_final_text,
            "get_google_calendar_busy_times": self.get_google_calendar_busy_times,
            "create_unregistered_time_slots": self.create_unregistered_time_slots,
            "create_final_time_slots": self.create_final_time_slots,
            "schedule_event": self.schedule_event,
            "send_event_invitation": self.send_event_invitation,
            "handle_scheduling_conflict": self.handle_scheduling_conflict,
            "send_chat_message_to_user": self.send_chat_message_to_user,
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
        start_date: str = None,
        end_date: str = None,
        message: str = None
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
        
        # Get conversation if exists
        conversations = await self.db_service.get_conversations_by_phone(phone_number)
        if conversations:
            conversation = conversations[0]
        else:
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
    
    # TODO: remove this
    async def send_confirmation_text(
        self,
        phone_number: str,
        message: str
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
            await self.texting_service.send_text(phone_number, message, final=False)
            
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
                "final": False
            }
        except Exception as e:
            raise RuntimeError(f"Failed to send message: {str(e)}")
    
    async def send_availability_text(
        self,
        phone_number: str,
        message: str
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
            await self.texting_service.send_text(phone_number, message, final=False)
            
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
                "final": False
            }
        except Exception as e:
            raise RuntimeError(f"Failed to send message: {str(e)}")
        
    async def send_final_text(
        self,
        phone_number: str,
        message: str
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
            await self.texting_service.send_text(phone_number, message, final=True)
            
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
                "final": True
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
        final_start: dict,
        final_end: dict,
        location: str = None,
        creator_message: str = None
    ) -> dict:
        """Schedule event with final details and notify participants. Returns updated event info and notification status."""
        try:
            # Validate the event exists and get its details
            print(f"Final start: {final_start}")
            print(f"Final end: {final_end}")
            event = await self.db_service.get_event_by_id(self.current_event_id)
            if not event:
                raise RuntimeError(f"Event {self.current_event_id} not found")
                
            # Get all participants
            participants = await self.db_service.get_event_participants(event_id)
            print(f"Participants: {participants}")
            # Send notifications to all participants
            attendees = []
            for participant in participants:
                if participant["status"] == "confirmed": # only include confirmed participants
                    await self.db_service.update_conversation(
                        event_id,
                        participant["phone_number"],
                        "active"
                    )

                    # create a google calendar event for registered users
                    if participant["registered"]: # only registered users have a calendarId
                        user = await self.db_service.get_user_by_phone(participant["phone_number"])
                        attendees.append(user["email"])
            print(f"Attendees: {attendees}")
            creator = await self.db_service.get_user_by_id(event["creator_id"])
            print(f"Creator: {creator}")
            final_start["dateTime"] = datetime.fromisoformat(final_start["dateTime"].replace("Z", "+00:00")).isoformat()
            final_end["dateTime"] = datetime.fromisoformat(final_end["dateTime"].replace("Z", "+00:00")).isoformat()

            await self.google_calendar_service.add_event(
                creator["google_access_token"],
                event["title"],
                final_start,
                final_end,
                attendees=attendees,
                location=location,
                description=event["description"]
            )
            print("added event to google calendar")
            # Update event with final details
            update_data = {
                "status": "scheduled",
                "final_start": final_start,
                "final_end": final_end,
                "location": location
            }
            print(f"Updating event: {update_data}")
            updated_event = await self.db_service.update_event(event_id, update_data)
            print(f"Updated event: {updated_event}")

            # Send final message to creator via chat
            final_message = f"Great! Your event '{event['title']}' has been scheduled for {final_start['dateTime']} - {final_end['dateTime']}"
            if location:
                final_message += f" at {location}"
            final_message += "."
            print(f"Sending final message to creator: {final_message}")
            await send_chat_message(creator["id"], final_message)

            # Send text messages to participants
            for participant in participants:
                if participant["status"] == "confirmed": # only confirmed participants
                    await self.send_final_text(
                        participant["phone_number"],
                        f"Scheduled {event['title']} with {creator['name']} for {final_start['dateTime']} - {final_end['dateTime']} at {location}.",
                        "final"
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
            await self.send_final_text(phone_number, message)
            
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
                    await self.send_final_text(phone_number, message)
                    
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
                await self.send_final_text(phone_number, message)
                
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
             if c["type"] in ["registered", "unregistered"] and c["status"] == "waiting_for_availability"),
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

    async def check_conversation_state(
        self,
        event_id: str,
        phone_numbers: list[str],
        current_stage: str
    ) -> dict:
        """Check the current state of the conversation and determine if the loop should continue or advance to the next stage."""
        try:
            # For other stages, we need an event
            if current_stage == "draft":
                if not event_id:
                    return {
                        "should_advance": False,
                        "reason": "Waiting for event creation",
                        "current_status": {
                            "event_status": None,
                            "participant_statuses": {},
                            "current_stage": current_stage
                        }
                    }
                elif not phone_numbers:
                    return {
                        "should_advance": False,
                        "reason": "Waiting for participants to be added",
                        "current_status": {
                            "event_status": None,
                            "participant_statuses": {},
                            "current_stage": current_stage
                        }
                    }
                else:
                    return {
                        "should_advance": True,
                        "reason": "Event creation and participant setup complete",
                        "current_status": {
                            "event_status": None,
                            "participant_statuses": {},
                            "current_stage": current_stage
                        }
                    }
            event = await self.db_service.get_event_by_id(event_id)
            if current_stage != "draft" and not event:
                raise RuntimeError(f"Event {event_id} not found")
            participants = await self.db_service.get_event_participants(event_id)
            participant_statuses = {p["phone_number"]: p["status"] for p in participants}

            should_advance = False
            reason = None

            if current_stage == "participant_setup":
                # Advance if all participants have been messaged (e.g., have a conversation started)
                all_messaged = True
                for phone in phone_numbers:
                    conversations = await self.db_service.get_conversations(event_id, phone)
                    if not any(c["type"] in ["registered", "unregistered"] for c in conversations):
                        all_messaged = False
                        break
                if all_messaged:
                    should_advance = True
                    reason = "All participants have been messaged."

            elif current_stage == "confirmation":
                # Advance if all participants have confirmed or declined
                all_responded = all(
                    participant_statuses.get(phone) in ["confirmed", "declined"]
                    for phone in phone_numbers
                )
                if all_responded:
                    should_advance = True
                    reason = "All participants have confirmed or declined."

            elif current_stage == "availability":
                # Advance if all participants have provided availability (status == 'availability_provided' or similar)
                all_provided = all(
                    participant_statuses.get(phone) in ["availability_provided", "confirmed", "declined"]
                    for phone in phone_numbers
                )
                if all_provided:
                    should_advance = True
                    reason = "All participants have provided availability or are not attending."

            elif current_stage == "scheduling":
                # Advance if event is scheduled
                if event["status"] == "scheduled":
                    should_advance = True
                    reason = "Event has been scheduled."

            return {
                "should_advance": should_advance,
                "reason": reason,
                "current_status": {
                    "event_status": event["status"],
                    "participant_statuses": participant_statuses,
                    "current_stage": current_stage
                }
            }
        except Exception as e:
            self._handle_error(e, "Failed to check conversation state")

    STAGES = [
        "draft",                # 1. Understand and draft
        "participant_setup",    # 2. Participant setup and Initial messaging
        "confirmation",         # 3. Confirmation Handling
        "availability",         # 4. Availability collection
        "scheduling"            # 5. Scheduling and Final notification
    ]

    TOOLS_FOR_STAGE = {
        "agent loop": [
            "create_draft_event", "search_contacts", "check_user_registration", "create_event_participant", "create_or_get_conversation", "send_chat_message_to_user", "send_confirmation_text"
        ],
        "participant_setup": [
            "create_event_participant", "create_or_get_conversation"
        ],
        "confirmation": [
            "send_confirmation_text", "handle_confirmation"
        ],
        "availability": [
            "get_google_calendar_busy_times", "create_unregistered_time_slots",
            "create_final_time_slots", "send_availability_text"
        ],
        "scheduling": [
            "schedule_event", "send_final_text"
        ]
    }

    async def run_agent_loop(self, user_input: str, creator_id: str, stage_limit=2, stage_idx=0):
        messages = [] # the messages to be sent to the agent. includes the system prompt, user input, previous assistant response, and all tool calls
        phone_numbers = set()  # Using set to avoid duplicates
        response = None # to save the last response from the agent
        step = 0 # to limit the total calls to the agent (for credits and development)
        tools = [tool for tool in [AVAILABLE_TOOLS[TOOL_NAME_TO_INDEX[tool_name]] for tool_name in self.TOOLS_FOR_STAGE["agent loop"] if tool_name in self.TOOL_MAPPINGS]]
        self._current_owner_id = creator_id
        tool_call_history = []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        creator = await self.db_service.get_user_by_id(creator_id)
        creator_name = creator["name"] if creator else "A friend"

        # Get current datetime in ISO format with timezone
        current_datetime = datetime.now().astimezone().isoformat()

        while stage_idx < stage_limit and step < 10:
            try:
                stage = self.STAGES[stage_idx]
                
                # For outbound messages, we don't wait for responses
                if step == 0:
                    messages = [
                        {"role": "system", "content": AVAILABLE_PROMPTS[stage].format(current_datetime=current_datetime)},
                        {"role": "user", "content": user_input + " (owner_name/creator_name: " + creator_name + "), (owner_id/creator_id [SECRET, DO NOT SHARE]: " + self._current_owner_id + ")"},
                    ]
                else:
                    messages = [
                        {"role": "system", "content": AVAILABLE_PROMPTS[stage].format(current_datetime=current_datetime)},
                        {"role": "user", "content": user_input + " (owner_name/creator_name: " + creator_name + "), (owner_id/creator_id [SECRET, DO NOT SHARE]: " + self._current_owner_id + ")"}
                    ]

                # Add previous response if exists
                if response:
                    content = str(response)
                    tool_calls = response.tool_calls
                    
                    for t in tool_call_history:
                        messages.append(t)
                    messages.append(content)
                    
                    # Handle tool calls
                    if tool_calls:
                        for tool_call in tool_calls:
                            print("<<<<<<<<<<<<<<<<<<<<<<<")
                            print(f"Tool call: {tool_call}")
                            print(">>>>>>>>>>>>>>>>>>>>>>>")
                            try:
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)
                                
                                if not tool_name or tool_name not in self.TOOL_MAPPINGS:
                                    logger.error(f"Invalid tool name: {tool_name}")
                                    continue
                                
                                # Execute tool and get response
                                tool_response = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                                
                                # Add tool response to messages
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": json.dumps(tool_response)
                                })
                                tool_call_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": json.dumps(tool_response)
                                })
                                
                                # Update phone numbers if tool returns them
                                if isinstance(tool_response, dict) and "phone_number" in tool_response:
                                    phone_numbers.add(tool_response["phone_number"])
                                    
                            except Exception as e:
                                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": json.dumps({"error": str(e)})
                                })
                    else: # logic for when to stop the agent loop (hopefully conversations are created)
                        break
                
                # Get next response from agent
                print(f"Stage {stage} messages: {messages}")
                response, usage = await self.prompt_agent(messages, tools)
                print("--------------------------------")
                print(f"Stage {stage} response: {response}")
                print("================================")
                
                total_prompt_tokens += usage.prompt_tokens
                total_completion_tokens += usage.completion_tokens
                step += 1
                    
            except Exception as e:
                logger.error(f"Error in agent loop at stage {stage}: {str(e)}")
                raise RuntimeError(f"Agent loop failed: {str(e)}")
                
        if stage_idx == stage_limit:
            self.stage_number = stage_idx - 1
        return {
            "success": True,
            "stage_idx": self.stage_number,
            "final_stage": self.STAGES[self.stage_number],
            "phone_numbers": list(phone_numbers),
            "event_id": self.current_event_id,
            "response": response,
            "step": step,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens
        }

    async def handle_inbound_message(self, phone_number: str, message: str) -> dict:
        """Handle an incoming text message from a participant"""
        try:
            # Find active conversation for this phone number
            conversations = await self.db_service.get_conversations_by_phone(phone_number)
            print(f"Conversations: {conversations}")
            active_conversation = next(
                (c for c in conversations if c["status"] == "active"),
                None
            )
            
            if not active_conversation:
                logger.warning(f"No active conversation found for {phone_number}")
                return {"message": message, "from_number": phone_number}
            
            # Save the user message to conversation history
            # user_message_obj = {
            #     "role": "user",
            #     "content": message,
            #     "timestamp": datetime.now().isoformat()
            # }
            # await self.db_service.append_conversation_message(active_conversation["id"], user_message_obj)
            
            # Set the current event from the conversation
            self.set_current_event(active_conversation["event_id"])
            
            # Get event and participant details
            now = datetime.now()
            current_datetime = now.astimezone().isoformat()
            event = await self.db_service.get_event_by_id(active_conversation["event_id"])
            print("got event")
            participant = await self.db_service.get_event_participant_by_phone(active_conversation["event_id"], phone_number)
            print("got participant")

            # Fetch last 10 messages for LLM context
            # conversation_history = await self.db_service.get_last_k_conversation_messages(active_conversation["id"], k=10)
            # # Build LLM context from conversation history
            # history_messages = [
            #     {"role": m["role"], "content": m["content"]} for m in conversation_history
            # ]

            creator = await self.db_service.get_user_by_id(event["creator_id"])
            name = creator["name"] if creator else "A friend"

            context = f"""Event: {event["title"]}
                \nEvent ID: {event["id"]}
                \nOwner ID: {event["creator_id"]}
                \nOwner Name: {name}
                \nPhone number: {phone_number}
                \nLast message sent to user: {active_conversation.get("last_message", "No previous message")}
                \nParticipant status: {participant["status"] if participant else "unknown"}
                \nUser replied: {message}
                """
            
            if participant["status"] == "pending_confirmation":
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
                tools = [AVAILABLE_TOOLS[TOOL_NAME_TO_INDEX["handle_confirmation"]]]
                print(f"Messages: {messages}")
                response, usage = await self.prompt_agent(messages, tools)
                print("--------------------------------")
                print(f"Response: {response}")
                print("================================")
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        print("<<<<<<<<<<<<<<<<<")
                        print(f"Tool call: {tool_call}")
                        print(">>>>>>>>>>>>>>>>>")
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        if tool_name in self.TOOL_MAPPINGS:
                            out = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                            print(f"Tool call output: {out}")
                
                if participant["status"] == "pending_availability":
                    if participant["registered"]: # TODO: test this
                        print("registered user")
                        messages = [
                            {
                                "role": "system",
                                "content": AVAILABLE_PROMPTS["availability"].format(current_datetime=current_datetime)
                            },
                            {
                                "role": "assistant",
                                "content": context
                            }
                        ]
                        tools = [AVAILABLE_TOOLS[TOOL_NAME_TO_INDEX["get_google_calendar_busy_times"]]]
                        print(f"Messages: {messages}")
                        response, usage = await self.prompt_agent(messages, tools)
                        print("--------------------------------")
                        print(f"Response: {response}")
                        print("================================")
                        if hasattr(response, 'tool_calls') and response.tool_calls:
                            for tool_call in response.tool_calls:
                                print("<<<<<<<<<<<<<<<<<")
                                print(f"Tool call: {tool_call}")
                                print(">>>>>>>>>>>>>>>>>")
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)
                                
                                if tool_name in self.TOOL_MAPPINGS:
                                    out = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                                    print(f"Tool call output: {out}")
                        update_data = {
                            "status": "pending_scheduling", 
                            "response_text": message,
                            "updated_at": now.isoformat(),
                        }
                        print(f"Updating event participant to pending_scheduling: {update_data}")
                        await self.db_service.update_event_participant(
                            self._current_event_id,
                            phone_number,
                            update_data
                        )
                        self._current_participants[phone_number].update(update_data)
                        return {"message": message, "from_number": phone_number}
                else:
                    print("unregistered user")
                    messages = [
                        {
                            "role": "system",
                            "content": AVAILABLE_PROMPTS["unregistered_availability"].format(current_datetime=current_datetime)
                        },
                        {
                            "role": "assistant",
                            "content": context
                        }
                    ]
                    tools = [AVAILABLE_TOOLS[TOOL_NAME_TO_INDEX["send_availability_text"]]]
                    print(f"Messages: {messages}")
                    response, usage = await self.prompt_agent(messages, tools)
                    print("--------------------------------")
                    print(f"Response: {response}")
                    print("================================")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        for tool_call in response.tool_calls:
                            print("<<<<<<<<<<<<<<<<<")
                            print(f"Tool call: {tool_call}")
                            print(">>>>>>>>>>>>>>>>>")
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
                        if tool_name in self.TOOL_MAPPINGS:
                            out = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                            print(f"Tool call output: {out}")
                        
                return {"message": message, "from_number": phone_number}
            
            elif participant["status"] == "pending_availability": # gets triggered for unregistered users, skipped by registered users
                messages = [
                    {
                        "role": "system",
                        "content": AVAILABLE_PROMPTS["availability_response"].format(current_datetime=current_datetime)
                    },
                    {
                        "role": "assistant",
                        "content": context
                    }
                ]
                tools = [AVAILABLE_TOOLS[TOOL_NAME_TO_INDEX["create_unregistered_time_slots"]]]
                print(f"Messages: {messages}")
                response, usage = await self.prompt_agent(messages, tools)
                print("--------------------------------")
                print(f"Response: {response}")
                print("================================")
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        print("<<<<<<<<<<<<<<<<<")
                        print(f"Tool call: {tool_call}")
                        print(">>>>>>>>>>>>>>>>>")
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                    if tool_name in self.TOOL_MAPPINGS:
                        out = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                        print(f"Tool call output: {out}")

                update_data = {
                    "status": "pending_scheduling", 
                    "response_text": message,
                    "updated_at": now.isoformat(),
                }
                print(f"Updating event participant: {update_data}")
                await self.db_service.update_event_participant(
                    self._current_event_id,
                    phone_number,
                    update_data
                )
                schedule_event = True
                print("checking if all participants are pending scheduling")
                participants = await self.db_service.get_event_participants(self._current_event_id)
                for p in participants:
                    if p["status"] != "pending_scheduling":
                        print(f"Participant {p['name']} is not pending scheduling")
                        schedule_event = False
                if schedule_event:
                    print("scheduling event")
                    participants = await self.db_service.get_event_participants(self._current_event_id)
                    for p in participants:
                        if p["status"] != "pending_scheduling":
                            return {"message": message, "from_number": phone_number}
                        
                    participant_times = {}
                    for p in participants:
                        if p["registered"]:
                            participant_times[p["name"]] = await self.db_service.get_participant_busy_times(self._current_event_id, p["phone_number"])
                        else:
                            participant_times[p["name"]] = await self.db_service.get_unregistered_time_slots(self._current_event_id, p["phone_number"])

                    context += f"\nParticipant times: {participant_times}"

                    messages = [
                        {
                            "role": "system",
                            "content": AVAILABLE_PROMPTS["scheduling"].format(current_datetime=current_datetime)
                        },  
                        {
                            "role": "assistant",
                            "content": context
                        }
                    ]
                    tools = [AVAILABLE_TOOLS[TOOL_NAME_TO_INDEX["schedule_event"]]] # TODO: have a way for the LLM to send a final text to all participants (for uniqueness)
                    print(f"Messages: {messages}")
                    response, usage = await self.prompt_agent(messages, tools)
                    print("--------------------------------")
                    print(f"Response: {response}")
                    print("================================")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        for tool_call in response.tool_calls:
                            print("<<<<<<<<<<<<<<<<<")
                            print(f"Tool call: {tool_call}")
                            print(">>>>>>>>>>>>>>>>>")
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
                            if tool_name in self.TOOL_MAPPINGS:
                                out = await self.TOOL_MAPPINGS[tool_name](**tool_args)
                                print(f"Tool call output: {out}")
                                creator_message = out["creator_message"]
                    now = datetime.now()
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
                    self._current_participants[phone_number].update(update_data)
                    
                    return {"message": message, "from_number": phone_number, "creator_message": creator_message}
            
            elif participant["status"] == "confirmed" or participant["status"] == "declined":
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