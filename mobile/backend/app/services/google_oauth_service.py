"""Google OAuth handler for calendar integration."""
# TODO: MAKE A WAY TO GET USER PHONE NUMBERS ON SIGN UP
import google.oauth2.credentials
import google_auth_oauthlib.flow
from typing import Optional
from urllib.parse import urlencode
from app.core.config import settings
import aiohttp
import google.auth.transport.requests

class GoogleOAuthHandler:
    """Handles Google OAuth2 flow for calendar integration."""
    
    def __init__(self):
        """Initialize the OAuth handler with settings from config."""
        print("Initializing OAuth handler with settings:")
        print(f"Client ID: {settings.GOOGLE_CLIENT_ID[:10]}...")  # Only log first 10 chars
        print(f"Auth URI: {settings.GOOGLE_AUTH_URI}")
        print(f"Token URI: {settings.GOOGLE_TOKEN_URI}")
        print(f"Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        print(f"Scopes: {settings.GOOGLE_CALENDAR_SCOPES}")
        
        self.flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": settings.GOOGLE_AUTH_URI,
                    "token_uri": settings.GOOGLE_TOKEN_URI,
                }
            },
            scopes=settings.GOOGLE_CALENDAR_SCOPES
        )
        self.flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        print("OAuth handler initialized successfully")

    def get_authorization_url(self) -> str:
        """Generate the Google OAuth authorization URL."""
        return self.flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

    def handle_callback(self, code: str) -> google.oauth2.credentials.Credentials:
        """Handle the OAuth callback and exchange code for tokens."""
        self.flow.fetch_token(code=code)
        return self.flow.credentials

    async def refresh_token(self, refresh_token: str) -> google.oauth2.credentials.Credentials:
        """Refresh an expired access token."""
        try:
            # Initialize credentials with all required fields
            credentials = google.oauth2.credentials.Credentials(
                None,  # No access token initially
                refresh_token=refresh_token,
                token_uri=settings.GOOGLE_TOKEN_URI,
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=settings.GOOGLE_CALENDAR_SCOPES
            )
            print("credentials", credentials)
            
            # Create a request object for token refresh
            request = google.auth.transport.requests.Request()
            
            # Request a new access token
            credentials.refresh(request)  # This is a synchronous call
            print("refreshed credentials token", credentials.token)
            print("refreshed credentials refresh_token", credentials.refresh_token)
            
            return credentials
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            raise
