"""Database service for Supabase operations."""
from supabase import create_client, Client
from core.config import settings
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

class DatabaseService:
    # Handles all database operations with Supabase
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    
    async def store_google_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime
    ) -> dict:
        # Store Google OAuth tokens for a user
        update_data = self.to_iso_strings({
            "google_access_token": access_token,
            "google_refresh_token": refresh_token,
            "google_token_expiry": token_expiry,
            "updated_at": datetime.now()
        })
        response = self.client.table("users").update(update_data).eq("id", user_id).execute()
        return self.from_iso_strings(response.data[0])
    
    async def get_google_tokens(self, user_id: str) -> dict:
        # Get Google OAuth tokens for a user
        response = self.client.table("users").select(
            "google_access_token",
            "google_refresh_token",
            "google_token_expiry"
        ).eq("id", user_id).execute()
        
        if not response.data:
            return None
            
        return self.from_iso_strings(response.data[0])
    
    def to_iso_strings(self, data: dict) -> dict:
        # Convert datetime objects to ISO strings
        return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in data.items()}

    def from_iso_strings(self, data: dict) -> dict:
        # Convert ISO strings back to datetime objects
        for k, v in data.items():
            if isinstance(v, str):
                try:
                    if len(v) >= 19 and v[4] == '-' and v[10] == 'T':
                        data[k] = datetime.fromisoformat(v)
                except Exception:
                    pass
        return data

    async def create_user(
        self,
        name: str,
        email: str = None
    ) -> dict:
        # Create a new user with optional email
        data = {
            "name": name,
            "email": email,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        data = self.to_iso_strings(data)
        response = self.client.table("users").insert(data).execute()
        return self.from_iso_strings(response.data[0])
    
    async def get_user_by_email(self, email: str) -> dict:
        # Get user by email address
        response = self.client.table("users").select("*").eq("email", email).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])
    
    async def get_or_create_user_by_email(self, email: str, name: str) -> dict:
        # Get existing user or create new one if not found
        response = self.client.table("users").select("*").eq("email", email).execute()
        
        if response.data:
            return self.from_iso_strings(response.data[0])
            
        return await self.create_user(name, email)

    async def get_user_by_phone(self, phone_number: str) -> dict:
        # Get user by phone number
        response = self.client.table("users").select("*").eq("phone_number", phone_number).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])
    
    async def get_availiability(self, event_id: str, start_date: str, end_date: str) -> dict:
        # Get availability for an event within date range
        response = self.client.table("availability").select("*").eq("event_id", event_id).eq("start_date", start_date).eq("end_date", end_date).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])

    async def get_event_by_id(self, event_id: str) -> Optional[dict]:
        # Get event by UUID
        response = self.client.table("events").select("*").eq("id", event_id).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])

    async def update_event(self, event_id: str, update_data: Dict[str, Any]) -> dict:
        # Update event with new data and refresh timestamp
        update_data["updated_at"] = datetime.now()
        update_data = self.to_iso_strings(update_data)
        
        response = self.client.table("events").update(update_data).eq("id", event_id).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to update event: {response.error.message}")
            
        if not response.data:
            raise RuntimeError(f"Event not found: {event_id}")
            
        return self.from_iso_strings(response.data[0])

    async def create_event_participant(
        self,
        event_id: str,
        phone_number: str,
        name: str
    ) -> dict:
        # Create a new event participant, checking if they're a registered user
        user = await self.get_user_by_phone(phone_number)
        
        data = {
            "id": user["id"] if user else None,  # NULL for unregistered users
            "event_id": event_id,
            "phone_number": phone_number,
            "name": name,
            "registered": bool(user),
            "status": "invited",
            "response_text": None,
            "availability_slots": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        data = self.to_iso_strings(data)
        response = self.client.table("event_participants").insert(data).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to create event participant: {response.error.message}")
            
        return self.from_iso_strings(response.data[0])
    
    async def get_event_participants(self, event_id: str) -> list[dict]:
        # Get all participants for an event
        response = self.client.table("event_participants").select("*").eq("event_id", event_id).execute()
        return [self.from_iso_strings(p) for p in response.data]

    async def create_draft_event(
        self,
        creator_id: str,
        title: str,
        description: str = None
    ) -> dict:
        # Create a draft event that can be completed later
        event = {
            "id": str(uuid4()),
            "creator_id": creator_id,
            "title": title,
            "description": description,
            "status": "pending",
            "proposed_times": [],
            "final_time": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        data = self.to_iso_strings(event)
        response = self.client.table("events").insert(data).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to create event: {response.error.message}")
            
        return self.from_iso_strings(response.data[0])

    async def search_contacts(
        self,
        owner_id: str,  # ID of the user who owns this contact list (always registered)
        query: str = None,
        min_relationship_score: float = None,
        recent_only: bool = False,
        limit: int = 15,
        days_ago: int = 30
    ) -> list[dict]:
        # Search contacts with flexible filtering and pagination
        query_builder = self.client.table("contacts").select("*").eq("owner_id", owner_id)
        
        if query:
            # Search in name and phone number using Postgres full-text search
            query_builder = query_builder.or_(f"name.ilike.%{query}%,phone_number.ilike.%{query}%")
            
        if min_relationship_score is not None:
            query_builder = query_builder.gte("relationship_score", min_relationship_score)
            
        if recent_only:
            # Get contacts with interactions in the last x days
            x_days_ago = (datetime.now() - timedelta(days=days_ago)).isoformat()
            query_builder = query_builder.gte("last_interaction", x_days_ago)
            
        # Order by relationship score and last interaction
        query_builder = query_builder.order("relationship_score", desc=True)
        query_builder = query_builder.order("last_interaction", desc=True)
        
        # Apply limit
        query_builder = query_builder.limit(limit)
        
        response = query_builder.execute()
        return [self.from_iso_strings(c) for c in response.data]

    async def store_participant_busy_times(
        self,
        event_id: str,
        participant_id: str,
        busy_slots: list[dict]
    ) -> dict:
        """Store busy time slots for an event participant.
        
        Args:
            event_id: UUID of the event
            participant_id: UUID of the participant
            busy_slots: List of busy time slots, each containing:
                - start_time: datetime
                - end_time: datetime
                - source: str (e.g. "calendar")
        """
        data = {
            "event_id": event_id,
            "participant_id": participant_id,
            "busy_slots": busy_slots,
            "updated_at": datetime.now()
        }
        data = self.to_iso_strings(data)
        
        # Upsert to handle both new and existing records
        response = self.client.table("availability").upsert(data).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to store busy times: {response.error.message}")
            
        return self.from_iso_strings(response.data[0])

    async def get_participant_busy_times(
        self,
        event_id: str,
        participant_id: str
    ) -> list[dict]:
        """Get stored busy time slots for an event participant."""
        response = self.client.table("availability").select("*").eq("event_id", event_id).eq("participant_id", participant_id).execute()
        
        if not response.data:
            return []
            
        return self.from_iso_strings(response.data[0]).get("busy_slots", [])

    async def get_all_participants_busy_times(
        self,
        event_id: str
    ) -> dict[str, list[dict]]:
        """Get busy time slots for all participants in an event.
        
        Returns:
            Dictionary mapping participant IDs to their busy time slots
        """
        response = self.client.table("availability").select("*").eq("event_id", event_id).execute()
        
        if not response.data:
            return {}
            
        # Convert to dictionary of participant_id -> busy_slots
        return {
            record["participant_id"]: self.from_iso_strings(record).get("busy_slots", [])
            for record in response.data
        }

    async def get_participants_busy_times_in_range(
        self,
        event_id: str,
        participant_ids: list[str],
        start_time: datetime,
        end_time: datetime
    ) -> dict[str, list[dict]]:
        """Get busy time slots for specific participants within a time range."""
        # Get all busy times for the event
        response = self.client.table("availability").select("*").eq("event_id", event_id).execute()
        
        if not response.data:
            return {}
            
        # Filter and process the results
        result = {}
        for record in response.data:
            participant_id = record["participant_id"]
            if participant_id not in participant_ids:
                continue
                
            # Get busy slots and convert to datetime objects
            busy_slots = self.from_iso_strings(record).get("busy_slots", [])
            
            # Filter slots that overlap with the time range
            overlapping_slots = []
            for slot in busy_slots:
                slot_start = datetime.fromisoformat(slot["start_time"])
                slot_end = datetime.fromisoformat(slot["end_time"])
                
                # Check if the slot overlaps with our time range
                if (slot_start <= end_time and slot_end >= start_time):
                    overlapping_slots.append(slot)
                    
            if overlapping_slots:
                result[participant_id] = overlapping_slots
                
        return result

    async def get_event_participant_by_phone(
        self,
        event_id: str,
        phone_number: str
    ) -> Optional[dict]:
        """Get an event participant by their phone number."""
        response = self.client.table("event_participants").select("*").eq("event_id", event_id).eq("phone_number", phone_number).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])

    async def create_conversation(
        self,
        event_id: str,
        phone_number: str,
        user_name: str,
        conversation_type: str,
        user_id: str = None
    ) -> dict:
        """Create a new conversation for an unregistered user."""
        data = {
            "event_id": event_id,
            "phone_number": phone_number,
            "user_name": user_name,
            "type": conversation_type,
            "user_id": user_id,
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        data = self.to_iso_strings(data)
        response = self.client.table("conversations").insert(data).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to create conversation: {response.error.message}")
            
        return self.from_iso_strings(response.data[0])

    async def store_unregistered_time_slots(
        self,
        event_id: str,
        phone_number: str,
        time_slots: list[dict]
    ) -> dict:
        """Store time slots (busy/available) for an unregistered user, including slot metadata like times, type, source, and confidence."""
        data = {
            "event_id": event_id,
            "phone_number": phone_number,
            "time_slots": time_slots,
            "updated_at": datetime.now()
        }
        data = self.to_iso_strings(data)
        
        # Upsert to handle both new and existing records
        response = self.client.table("unregistered_time_slots").upsert(data).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to store time slots: {response.error.message}")
            
        return self.from_iso_strings(response.data[0])

    async def get_unregistered_time_slots(
        self,
        event_id: str,
        phone_number: str
    ) -> list[dict]:
        """Get stored time slots for an unregistered user."""
        response = self.client.table("unregistered_time_slots").select("*").eq("event_id", event_id).eq("phone_number", phone_number).execute()
        
        if not response.data:
            return []
            
        return self.from_iso_strings(response.data[0]).get("time_slots", [])

    async def get_all_unregistered_time_slots(
        self,
        event_id: str
    ) -> dict[str, list[dict]]:
        """Get all unregistered users' time slots for an event, returned as phone_number -> slots dict."""
        response = self.client.table("unregistered_time_slots").select("*").eq("event_id", event_id).execute()
        
        if not response.data:
            return {}
            
        # Convert to dictionary of phone_number -> time_slots
        return {
            record["phone_number"]: self.from_iso_strings(record).get("time_slots", [])
            for record in response.data
        }

    async def get_unregistered_time_slots_in_range(
        self,
        event_id: str,
        phone_numbers: list[str],
        start_time: datetime,
        end_time: datetime
    ) -> dict[str, list[dict]]:
        """Get time slots for specific unregistered users within a time range."""
        # Get all time slots for the event
        response = self.client.table("unregistered_time_slots").select("*").eq("event_id", event_id).execute()
        
        if not response.data:
            return {}
            
        # Filter and process the results
        result = {}
        for record in response.data:
            phone_number = record["phone_number"]
            if phone_number not in phone_numbers:
                continue
                
            # Get time slots and convert to datetime objects
            time_slots = self.from_iso_strings(record).get("time_slots", [])
            
            # Filter slots that overlap with the time range
            overlapping_slots = []
            for slot in time_slots:
                slot_start = datetime.fromisoformat(slot["start_time"])
                slot_end = datetime.fromisoformat(slot["end_time"])
                
                # Check if the slot overlaps with our time range
                if (slot_start <= end_time and slot_end >= start_time):
                    overlapping_slots.append(slot)
                    
            if overlapping_slots:
                result[phone_number] = overlapping_slots
                
        return result

    async def get_conversations(
        self,
        event_id: str,
        phone_number: str
    ) -> list[dict]:
        """Get all conversations for an unregistered user in an event."""
        response = self.client.table("conversations").select("*").eq("event_id", event_id).eq("phone_number", phone_number).execute()
        return [self.from_iso_strings(c) for c in response.data]

    async def update_conversation_status(
        self,
        event_id: str,
        phone_number: str,
        status: str,
        user_name: str = None
    ) -> dict:
        """Update the status of a conversation."""
        data = {
            "status": status,
            "updated_at": datetime.now()
        }
        if user_name:
            data["user_name"] = user_name
            
        data = self.to_iso_strings(data)
        
        response = self.client.table("conversations").update(data).eq("event_id", event_id).eq("phone_number", phone_number).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to update conversation status: {response.error.message}")
            
        return self.from_iso_strings(response.data[0])

    async def update_event_participant(
        self,
        event_id: str,
        phone_number: str,
        update_data: Dict[str, Any]
    ) -> dict:
        """Update an event participant's information.
        
        Args:
            event_id: UUID of the event
            phone_number: Phone number of the participant
            update_data: Dictionary of fields to update
        """
        update_data["updated_at"] = datetime.now()
        update_data = self.to_iso_strings(update_data)
        
        response = self.client.table("event_participants").update(update_data).eq("event_id", event_id).eq("phone_number", phone_number).execute()
        
        if response.error:
            raise RuntimeError(f"Failed to update event participant: {response.error.message}")
            
        if not response.data:
            raise RuntimeError(f"Event participant not found: {event_id} - {phone_number}")
            
        return self.from_iso_strings(response.data[0])