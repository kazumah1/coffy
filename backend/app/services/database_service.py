"""Database service for Supabase operations."""
#TODO: ADD A WAY TO UPDATE CONTACTS ON USER SIGN UP (TO BE REGISTERED)
from supabase import create_client, Client
from app.core.config import settings
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
        """Convert datetime objects to ISO strings, handling nested structures."""
        def convert_value(v):
            if isinstance(v, datetime):
                return v.isoformat()
            elif isinstance(v, dict):
                return {k: convert_value(val) for k, val in v.items()}
            elif isinstance(v, list):
                return [convert_value(item) for item in v]
            return v
            
        return {k: convert_value(v) for k, v in data.items()}

    def from_iso_strings(self, data: dict) -> dict:
        """Convert ISO strings back to datetime objects, handling nested structures."""
        def convert_value(v):
            if isinstance(v, str):
                try:
                    # Check if the string matches ISO format (YYYY-MM-DDTHH:MM:SS)
                    if len(v) >= 19 and v[4] == '-' and v[10] == 'T':
                        return datetime.fromisoformat(v)
                except Exception:
                    pass
            elif isinstance(v, dict):
                return {k: convert_value(val) for k, val in v.items()}
            elif isinstance(v, list):
                return [convert_value(item) for item in v]
            return v
            
        return {k: convert_value(v) for k, v in data.items()}

    async def create_user(
        self,
        name: str,
        email: str = None
    ) -> dict:
        # Create a new user with optional email
        data = {
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "contacts_loaded": False
        }
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
    
    async def get_user_by_id(self, user_id: str) -> dict:
        # Get user by ID
        response = self.client.table("users").select("*").eq("id", user_id).execute()
        if not response.data:
            return None
        return response.data[0]

    async def update_user(self, user_id: str, name: str, email: str, phone_number: str, contacts_loaded: bool) -> dict:
        # Update user by ID
        update_data = {}
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if phone_number:
            update_data["phone_number"] = phone_number
        if contacts_loaded:
            update_data["contacts_loaded"] = contacts_loaded
        response = self.client.table("users").update(update_data).eq("id", user_id).execute()
        if not response.data:
            return None
        
        contact_response = self.client.table("contacts").select("*").eq("phone_number", phone_number).execute()
        if contact_response.data:
            for contact in contact_response.data:
                contact["updated_at"] = datetime.now().isoformat()
                self.client.table("contacts").update(contact).eq("recipient_id", user_id).execute()

        return response.data[0]
    
    async def get_user_by_google_id(self, google_id: str) -> dict:
        # Get user by Google ID
        response = self.client.table("users").select("*").eq("google_id", google_id).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])

    async def get_user_by_phone(self, phone_number: str) -> dict:
        # Get user by phone number
        response = self.client.table("users").select("*").eq("phone_number", phone_number).execute()
        if not response.data:
            return None
        return response.data[0]
    
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
        now = datetime.now()
        update_data["updated_at"] = now.isoformat()
        update_data = self.to_iso_strings(update_data)
        
        response = self.client.table("events").update(update_data).eq("id", event_id).execute()
        
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
        
        now = datetime.now()
        event_participant = {
            "id": str(uuid4()),
            "user_id": user["id"] if user else None,  # NULL for unregistered users
            "event_id": event_id,
            "phone_number": phone_number,
            "name": name,
            "registered": bool(user),
            "status": "pending_confirmation", # pending_confirmation, pending_availability, pending_scheduling, confirmed, declined
            "response_text": None,
            "availability_slots": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        response = self.client.table("event_participants").insert(event_participant).execute()
        
        if not response.data:
            raise RuntimeError(f"Failed to create event participant for event {event_id} and phone {phone_number}")
            
        return event_participant
    
    async def get_event_participants(self, event_id: str) -> list[dict]:
        # Get all participants for an event
        response = self.client.table("event_participants").select("*").eq("event_id", event_id).execute()
        return [p for p in response.data]

    async def create_draft_event(
        self,
        creator_id: str,
        title: str,
        description: str = None
    ) -> dict:
        # Create a draft event that can be completed later
        now = datetime.now()
        event = {
            "id": str(uuid4()),
            "creator_id": creator_id,
            "title": title,
            "description": description,
            "status": "pending",
            "proposed_times": [],
            "final_start": None,
            "final_end": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "stage": 0,
        }
        
        # Convert all datetime objects to ISO format strings

        response = self.client.table("events").insert(event).execute()
        
        if not response.data:
            raise RuntimeError("Failed to create event: No data returned from database")
            
        return event

    async def search_contacts(
        self,
        owner_id: str,  # ID of the user who owns this contact list (always registered)
        query: str = None,
        min_relationship_score: float = None,
        recent_only: bool = False,
        limit: int = 15,
        days_ago: int = 30
    ) -> list[dict]:
        """Search contacts with flexible filtering and pagination."""
        try:
            query_builder = self.client.table("contacts").select("*").eq("owner_id", owner_id)
            
            if query:
                # Search in name and phone number using Postgres full-text search
                query_builder = query_builder.or_(f"name.ilike.%{query}%,phone_number.ilike.%{query}%")
                
            if min_relationship_score is not None:
                query_builder = query_builder.gte("relationship_score", min_relationship_score)
                
            # TODO: add recent only and last interaction query (implemented using datetime in isoformat and then logic handled here)
            # Order by relationship score and last interaction
            query_builder = query_builder.order("relationship_score", desc=True)
            
            # Apply limit
            query_builder = query_builder.limit(limit)
            
            response = query_builder.execute()
            
            # The response.data will be None if there was an error
            if response.data is None:
                print("response.data is None")
                raise RuntimeError("Failed to search contacts: No data returned")
                
        except Exception as e:
            print("exception", e)
            raise RuntimeError(f"Failed to search contacts: {e}")
            
        # Convert all datetime fields in the response
        return [c for c in response.data]

    async def store_participant_busy_times(
        self,
        event_id: str,
        participant_id: str,
        busy_slots: list[dict]
    ) -> dict:
        """Store busy time slots for an event participant."""
        now = datetime.now()
        data = {
            "event_id": event_id,
            "participant_id": participant_id,
            "busy_slots": busy_slots,
            "updated_at": now.isoformat()
        }
        data = self.to_iso_strings(data)
        
        # Upsert to handle both new and existing records
        response = self.client.table("availability").upsert(data).execute()
        
        if not response.data:
            raise RuntimeError(f"Failed to store busy times for event {event_id} and participant {participant_id}")
            
        return data

    async def get_participant_busy_times(
        self,
        event_id: str,
        participant_id: str
    ) -> list[dict]:
        """Get stored busy time slots for an event participant."""
        response = self.client.table("availability").select("*").eq("event_id", event_id).eq("participant_id", participant_id).execute()
        
        if not response.data:
            return []
            
        return response.data[0].get("busy_slots", [])

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
            record["participant_id"]: record.get("busy_slots", [])
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
        return response.data[0]

    async def create_conversation(
        self,
        event_id: str,
        phone_number: str,
        user_name: str,
        conversation_type: str,
        user_id: str = None
    ) -> dict:
        """Create a new conversation for an unregistered user."""
        now = datetime.now()
        conversation = {
            "id": str(uuid4()),
            "event_id": event_id,
            "phone_number": phone_number,
            "user_id": user_id,
            "user_name": user_name,
            "type": conversation_type,
            "status": "active",
            "last_message": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        response = self.client.table("conversations").insert(conversation).execute()
        
        if not response.data:
            raise RuntimeError(f"Failed to create conversation for event {event_id} and phone {phone_number}")
            
        return conversation

    async def store_unregistered_time_slots(
        self,
        event_id: str,
        phone_number: str,
        time_slots: list[dict]
    ) -> dict:
        """Store time slots for an unregistered user."""
        now = datetime.now()
        data = {
            "id": str(uuid4()),
            "event_id": event_id,
            "phone_number": phone_number,
            "time_slots": time_slots,
            "updated_at": now.isoformat()
        }
        
        # Upsert to handle both new and existing records
        response = self.client.table("unregistered_time_slots").upsert(
            data,
            on_conflict="event_id,phone_number"
        ).execute()
        
        if not response.data:
            raise RuntimeError(f"Failed to store time slots for event {event_id} and phone {phone_number}")
            
        return data

    async def get_unregistered_time_slots(
        self,
        event_id: str,
        phone_number: str
    ) -> list[dict]:
        """Get stored time slots for an unregistered user."""
        response = self.client.table("unregistered_time_slots").select("*").eq("event_id", event_id).eq("phone_number", phone_number).execute()
        
        if not response.data:
            return []
            
        return response.data[0].get("time_slots", [])

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
            record["phone_number"]: record.get("time_slots", [])
            for record in response.data
        }
    
    async def delete_event_unregistered_time_slots(
        self,
        event_id: str
    ) -> dict:
        """Delete all unregistered users' time slots for an event."""
        response = self.client.table("unregistered_time_slots").delete().eq("event_id", event_id).execute()
        
        if not response.data:
            return None
            
        return response.data

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
            time_slots = record.get("time_slots", [])
            
            # Filter slots that overlap with the time range
            overlapping_slots = []
            for slot in time_slots:
                slot_start = datetime.fromisoformat(slot["start_time"])
                slot_end = datetime.fromisoformat(slot["end_time"])
                
                # Check if the slot overlaps with our time range
                if (slot_start <= end_time and slot_end >= start_time):
                    overlapping_slots.append(slot.isoformat())
                    
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

    async def update_conversation(
        self,
        event_id: str,
        phone_number: str,
        status: str,
        user_name: str = None,
        last_message: str = None
    ) -> dict:
        """Update the status of a conversation."""
        now = datetime.now()
        conversation = {
            "status": status,
            "updated_at": now.isoformat()
        }
        if user_name:
            conversation["user_name"] = user_name
        if last_message:
            conversation["last_message"] = last_message
        
        current_conversation = await self.client.table
        
        response = self.client.table("conversations").update(conversation).eq("event_id", event_id).eq("phone_number", phone_number).execute()
        
        if not response.data:
            raise RuntimeError(f"Failed to update conversation for event {event_id} and phone {phone_number}")
            
        return conversation

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
        now = datetime.now()
        update_data["updated_at"] = now.isoformat()
        print("putting update data into supabase")
        response = self.client.table("event_participants").update(update_data).eq("event_id", event_id).eq("phone_number", phone_number).execute()
        
        print("response", response)
        if not response.data:
            raise RuntimeError(f"Failed to update event participant for event {event_id} and phone {phone_number}")
            
        return response.data[0]

    # Contacts management methods
    async def create_contact(self, contact_data: dict) -> dict:
        """Create a new contact"""
        now = datetime.now()
        contact = {
            "id": str(uuid4()),
            "owner_id": contact_data["owner_id"],
            "name": contact_data["name"],
            "phone_number": contact_data["phone_number"],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        print("contact_data", contact_data)
        # Check if any phone number belongs to a registered user
        check_registered = await self.get_user_by_phone(contact_data["phone_number"])
        print("check_registered", check_registered)
        if check_registered:
            contact["recipient_id"] = check_registered["id"]
        else:
            contact["recipient_id"] = None

        response = self.client.table("contacts").insert(contact).execute()
        print("response", response)
        if not response.data:
            raise RuntimeError(f"Failed to create contact for owner {contact_data['owner_id']} and phone {contact_data['phone_number']}")
            
        return contact

    async def update_contact(self, contact_id: str, contact_data: dict) -> dict:
        """Update an existing contact"""
        now = datetime.now()
        update_data = {
            "name": contact_data["name"],
            "phone_number": contact_data["phone_number"],
            "updated_at": now.isoformat()
        }
        print("update_data", update_data)
        # Check if any phone number belongs to a registered user
        check_registered = await self.get_user_by_phone(contact_data["phone_number"])
        print("check_registered update", check_registered)
        if check_registered:
            update_data["recipient_id"] = check_registered["id"]
        else:
            update_data["recipient_id"] = None
        
        response = self.client.table("contacts").update(update_data).eq("id", contact_id).execute()
        print("response", response)
        if not response.data:
            raise RuntimeError(f"Failed to update contact {contact_id}")
            
        return update_data

    async def get_contact_by_device_id(self, owner_id: str, device_contact_id: str) -> dict:
        """Get contact by device contact ID"""
        response = self.client.table("contacts").select("*").eq("owner_id", owner_id).eq("device_contact_id", device_contact_id).execute()
        
        if not response.data:
            return None
            
        return response.data[0]

    async def get_user_contacts(self, owner_id: str) -> list[dict]:
        """Get all contacts for a user"""
        response = self.client.table("contacts").select("*").eq("owner_id", owner_id).execute()
        if not response.data:
            return []
        return [c for c in response.data]

    # TODO: not for MVP
    async def add_best_friend(self, user_id: str, contact_id: str) -> dict:
        """Add a contact as a best friend"""
        now = datetime.now()
        best_friend = {
            "id": str(uuid4()),
            "user_id": user_id,
            "contact_id": contact_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        response = self.client.table("best_friends").insert(best_friend).execute()
        
        if not response.data:
            raise RuntimeError(f"Failed to add best friend")
            
        return self.from_iso_strings(response.data[0])

    # TODO: not for MVP
    async def clear_best_friends(self, user_id: str) -> bool:
        """Clear all best friends for a user"""
        response = self.client.table("best_friends").delete().eq("user_id", user_id).execute()
        return True

    # TODO: not for MVP
    async def get_best_friends(self, user_id: str) -> list[dict]:
        """Get all best friends for a user"""
        response = self.client.table("best_friends").select("*").eq("user_id", user_id).execute()
        return [self.from_iso_strings(bf) for bf in response.data]

    # TODO: not for MVP
    async def get_best_friends_with_details(self, user_id: str) -> list[dict]:
        """Get all best friends with contact details"""
        response = self.client.table("best_friends").select(
            """
            *,
            contacts:contact_id (
                id,
                device_contact_id,
                name,
                phone_numbers,
                emails
            )
            """
        ).eq("user_id", user_id).execute()
        
        best_friends = []
        for bf in response.data:
            if bf.get("contacts"):
                contact = bf["contacts"]
                # Flatten the structure
                best_friend = {
                    "id": contact["id"],
                    "device_contact_id": contact["device_contact_id"],
                    "name": contact["name"],
                    "phone_numbers": contact["phone_numbers"],
                    "emails": contact["emails"]
                }
                best_friends.append(self.from_iso_strings(best_friend))
        
        return best_friends

    async def get_events_by_participant_phone(self, phone_number: str) -> list[dict]:
        """Get all events where a phone number is a participant."""
        # First get all event participants with this phone number
        response = self.client.table("event_participants").select(
            "event_id"
        ).eq("phone_number", phone_number).execute()
        
        if not response.data:
            return []
            
        # Get the events for these participants
        event_ids = [p["event_id"] for p in response.data]
        events_response = self.client.table("events").select("*").in_("id", event_ids).execute()
        
        if not events_response.data:
            return []
            
        return [event for event in events_response.data]

    async def get_conversation_by_phone(self, phone_number: str) -> list[dict]:
        """Get all conversations for a phone number."""
        response = self.client.table("conversations").select("*").eq("phone_number", phone_number).execute()
        return response.data[0] if response.data else None

    K = 10  # Number of messages to keep per conversation

    async def append_conversation_message(self, conversation_id: str, message: dict, k: int = K) -> dict:
        """Append a message to the conversation's messages array, keeping only the last k messages."""
        response = self.client.table("conversations").select("messages").eq("id", conversation_id).execute()
        messages = response.data[0]["messages"] if response.data and response.data[0].get("messages") else []
        messages.append(message)
        messages = messages[-k:]
        update_resp = self.client.table("conversations").update({"messages": messages}).eq("id", conversation_id).execute()
        return update_resp.data[0] if update_resp.data else None

    async def get_last_k_conversation_messages(self, conversation_id: str, k: int = K) -> list:
        response = self.client.table("conversations").select("messages").eq("id", conversation_id).execute()
        messages = response.data[0]["messages"] if response.data and response.data[0].get("messages") else []
        return messages[-k:]
    
    async def get_last_k_chat_session_messages(self, chat_session_id: str, k: int = K) -> list:
        response = self.client.table("chat_sessions").select("messages").eq("id", chat_session_id).execute()
        messages = response.data[0]["messages"] if response.data and response.data[0].get("messages") else []
        return messages[-k:]

    async def extend_chat_session_message(self, chat_session_id: str, messages: list) -> dict:
        """Extend the chat session's messages array."""
        response = self.client.table("chat_sessions").select("messages").eq("id", chat_session_id).execute()
        messages = response.data[0]["messages"] if response.data and response.data[0].get("messages") else []
        messages.extend(messages)
        response = self.client.table("chat_sessions").update({"messages": messages}).eq("id", chat_session_id).execute()
        return response.data[0] if response.data else None