from fastapi import Depends
from services.database_service import DatabaseService
from services.google_oauth_service import GoogleOAuthHandler
from services.google_calendar_service import GoogleCalendarService
from services.token_manager import TokenManager

def get_database_service():
    return DatabaseService()

def get_oauth_handler():
    return GoogleOAuthHandler()

def get_token_manager(
    db_service: DatabaseService = Depends(get_database_service),
    oauth_handler: GoogleOAuthHandler = Depends(get_oauth_handler)
):
    return TokenManager(db_service, oauth_handler)

def get_google_calendar_service():
    return GoogleCalendarService()