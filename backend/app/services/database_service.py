"""Database service for Supabase operations."""
from supabase import create_client, Client
from core.config import settings
from datetime import datetime
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
        # Create a new event participant
        # First check if user exists with this phone number
        user = await self.get_user_by_phone(phone_number)
        
        data = {
            "id": user["id"] if user else str(uuid4()),
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