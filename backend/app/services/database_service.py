"""Database service for Supabase operations."""
from supabase import create_client, Client
from core.config import settings
from datetime import datetime

class DatabaseService:
    """Handles all database operations with Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
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
        """Store Google OAuth tokens for a user.
        
        Args:
            user_id: The user's UUID
            access_token: Google access token
            refresh_token: Google refresh token
            token_expiry: Token expiry timestamp
        """
        # Convert datetime to ISO string before storing
        update_data = self.to_iso_strings({
            "google_access_token": access_token,
            "google_refresh_token": refresh_token,
            "google_token_expiry": token_expiry,
            "updated_at": datetime.now()
        })
        response = self.client.table("users").update(update_data).eq("id", user_id).execute()
        return self.from_iso_strings(response.data[0])
    
    async def get_google_tokens(self, user_id: str) -> dict:
        """Get Google OAuth tokens for a user.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            Dictionary containing tokens and expiry
        """
        response = self.client.table("users").select(
            "google_access_token",
            "google_refresh_token",
            "google_token_expiry"
        ).eq("id", user_id).execute()
        
        if not response.data:
            return None
            
        return self.from_iso_strings(response.data[0])
    
    def to_iso_strings(self, data: dict) -> dict:
        # Convert all datetime objects in a dict to ISO strings
        return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in data.items()}

    def from_iso_strings(self, data: dict) -> dict:
        # Convert all ISO string fields in a dict back to datetime objects if possible
        for k, v in data.items():
            if isinstance(v, str):
                try:
                    # Only convert if it looks like an ISO datetime
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
        """Create a new user.
        
        Args:
            name: User's name
            email: User's email (optional)
            
        Returns:
            Created user data
        """
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
        """Get user by email.
        
        Args:
            email: User's email
            
        Returns:
            User data if found, None otherwise
        """
        response = self.client.table("users").select("*").eq("email", email).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])
    
    async def get_or_create_user_by_email(self, email: str, name: str) -> dict:
        # First try to find user
        response = self.client.table("users").select("*").eq("email", email).execute()
        
        if response.data:
            return self.from_iso_strings(response.data[0])
            
        # If not found, create new user
        return await self.create_user(name, email)

    async def get_user_by_phone(self, phone_number: str) -> dict:
        response = self.client.table("users").select("*").eq("phone_number", phone_number).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])
    
    async def get_availiability(self, event_id: str, start_date: str, end_date: str) -> dict:
        response = self.client.table("availability").select("*").eq("event_id", event_id).eq("start_date", start_date).eq("end_date", end_date).execute()
        if not response.data:
            return None
        return self.from_iso_strings(response.data[0])