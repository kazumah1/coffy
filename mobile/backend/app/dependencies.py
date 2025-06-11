from fastapi import Depends
from app.services.database_service import DatabaseService
from app.services.google_oauth_service import GoogleOAuthHandler
from app.services.token_manager import TokenManager
from app.services.google_calendar_service import GoogleCalendarService
from app.services.texting_service import TextingService
from app.services.openrouter_service import OpenRouterService

# Global instances to handle circular dependency
_db_service = None
_oauth_handler = None
_token_manager = None
_google_calendar_service = None
_texting_service = None
_openrouter_service = None

# Singleton getters
def get_database_service():
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

def get_oauth_handler():
    global _oauth_handler
    if _oauth_handler is None:
        _oauth_handler = GoogleOAuthHandler()
    return _oauth_handler

def get_token_manager():
    global _token_manager
    if _token_manager is None:
        db = get_database_service()
        oauth = get_oauth_handler()
        _token_manager = TokenManager(db, oauth)
    return _token_manager

def get_google_calendar_service():
    global _google_calendar_service
    if _google_calendar_service is None:
        _google_calendar_service = GoogleCalendarService()
    return _google_calendar_service

def get_texting_service():
    global _texting_service
    if _texting_service is None:
        db = get_database_service()
        # Get OpenRouter service first to avoid circular dependency issues
        openrouter = get_openrouter_service()
        _texting_service = TextingService(db_service=db, openrouter_service=openrouter)
    return _texting_service

def get_openrouter_service():
    global _openrouter_service
    if _openrouter_service is None:
        db = get_database_service()
        calendar = get_google_calendar_service()
        token = get_token_manager()
        _openrouter_service = OpenRouterService(db, calendar, token, None)  # Initialize without TextingService
    return _openrouter_service

# FastAPI dependency functions
def get_db_service_dependency():
    return get_database_service()

def get_oauth_handler_dependency():
    return get_oauth_handler()

def get_token_manager_dependency():
    return get_token_manager()

def get_google_calendar_service_dependency():
    return get_google_calendar_service()

def get_texting_service_dependency():
    return get_texting_service()

def get_openrouter_service_dependency():
    return get_openrouter_service()

# Initialize all services at startup
def initialize_services():
    """Initialize all services at application startup"""
    # Initialize in dependency order
    db = get_database_service()
    oauth = get_oauth_handler()
    calendar = get_google_calendar_service()
    token = get_token_manager()
    # Initialize OpenRouter first
    openrouter = get_openrouter_service()
    # Then initialize Texting with OpenRouter
    text = get_texting_service()
    # Now set up the circular dependency
    openrouter.texting_service = text
    
    # Verify all services are initialized
    assert db is not None, "Database service not initialized"
    assert oauth is not None, "OAuth handler not initialized"
    assert calendar is not None, "Calendar service not initialized"
    assert token is not None, "Token manager not initialized"
    assert text is not None, "Texting service not initialized"
    assert openrouter is not None, "OpenRouter service not initialized"