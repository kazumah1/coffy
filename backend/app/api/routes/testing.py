from fastapi import APIRouter, Depends
from app.services.database_service import DatabaseService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.services.texting_service import TextingService
from app.services.openrouter_service import OpenRouterService
from app.dependencies import (
    get_database_service,
    get_google_calendar_service,
    get_token_manager,
    get_texting_service,
    get_openrouter_service
)

router = APIRouter()

@router.get("/test-user-retrieval")
async def test_user_retrieval(phone_number: str, id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    # Start the agent loop in the background
    response =  await db_service.get_user_by_id(id)

    return response["name"]

@router.get("/test-schedule-event")
async def test_schedule_event(
    db_service: DatabaseService = Depends(get_database_service),
    token_manager: TokenManager = Depends(get_token_manager),
    google_calendar_service: GoogleCalendarService = Depends(get_google_calendar_service),
    texting_service: TextingService = Depends(get_texting_service),
    openrouter_service: OpenRouterService = Depends(get_openrouter_service)
):
    response = await openrouter_service.schedule_event(
        "f38e786a-e538-41e7-b9ff-cf07066e2fb6",
        {
            "dateTime": "2025-06-03T12:00:00Z",
            "timeZone": "America/New_York"
        },
        {
            "dateTime": "2025-06-03T13:00:00Z",
            "timeZone": "America/New_York"
        }
    )
    return response