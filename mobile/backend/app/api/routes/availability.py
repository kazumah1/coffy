from fastapi import APIRouter, HTTPException, Depends
from app.services.database_service import DatabaseService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.dependencies import get_database_service, get_google_calendar_service, get_token_manager

router = APIRouter()

@router.get("/{user_id}")
async def get_availability(
    user_id: str,
    start_date: str,
    end_date: str,
    db_service: DatabaseService = Depends(get_database_service),
    google_calendar_service: GoogleCalendarService = Depends(get_google_calendar_service),
    token_manager: TokenManager = Depends(get_token_manager)
):
    tokens = await token_manager.get_token(user_id)
    if not tokens:
        print("Token not found")
        raise HTTPException(status_code=401, detail="Token not found")
    events = google_calendar_service.get_all_events(tokens['google_access_token'], start_date, end_date)
    return events