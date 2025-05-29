from fastapi import APIRouter, HTTPException, Depends
from services.database_service import DatabaseService
from services.google_calendar_service import GoogleCalendarService
from services.token_manager import TokenManager
from dependencies import get_database_service, get_google_calendar_service, get_token_manager

router = APIRouter()

@router.get("/{event_id}")
async def get_availability(
    user_id: str,
    start_date: str,
    end_date: str,
    db_service: DatabaseService = Depends(get_database_service),
    google_calendar_service: GoogleCalendarService = Depends(get_google_calendar_service),
    token_manager: TokenManager = Depends(get_token_manager)
):
    tokens = get_google_tokens(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="User not found")
    
    if tokens["expired"]:
        tokens = refresh_google_tokens(user_id)
        if not tokens:
            raise HTTPException(status_code=401, detail="User not found")
    
    freebusy = get_freebusy(tokens["access_token"], start_date, end_date)
    return freebusy